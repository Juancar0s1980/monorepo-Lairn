"""
Asignación masiva de docentes a asignaturas de la malla (ADR-017).

Modelo existente (no se crea uno paralelo): una asignatura tiene docente
cuando `AsignaturaMalla.curso_vinculado` apunta a un `Curso` cuyo `docente`
es esa persona. Es lo mismo que hace la asignación individual (editar la
asignatura y elegir el curso), así que el banco de preguntas, las tareas, la
convocatoria y la analítica siguen funcionando igual.

Una fila = {asignatura_codigo, docente_email, curso_codigo?}. Para cada una:
  1. Se valida (vacíos, correo, docente activo con rol Docente, asignatura
     existente, activa y del programa elegido, curso del docente, repetidos).
  2. Se decide el curso:
       - `curso_codigo` dado → ese curso (debe ser del docente);
       - sin código → el curso del docente que ya implementa la asignatura, o
         uno del docente con el mismo nombre, o uno NUEVO con el nombre de la
         asignatura (se avisa en la vista previa: "se creará el curso…").
  3. Estado: valida | advertencia (se aplica; crea curso o cambia de docente)
     | ya_asignada | omitida (sin docente en la fila) | error.

Dos fases, como el importador de pensum: `planificar` no escribe; `aplicar`
escribe todo o nada (transaction.atomic). `huella` asegura que se confirma
exactamente lo que se revisó.
"""

import csv
import hashlib
import io
import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction

from apps.evaluacion_resultados.models import AsignaturaMalla

MAX_FILAS = 2000
MAX_BYTES = 2 * 1024 * 1024
ROL_DOCENTE = 'Docente'
COLUMNAS = {
    'asignatura_codigo': {'asignatura_codigo', 'codigo_asignatura', 'codigo asignatura', 'asignatura codigo',
                          'codigo', 'asignatura'},
    'docente_email': {'docente_email', 'correo_docente', 'email_docente', 'correo docente', 'email docente',
                      'docente', 'correo', 'email'},
    'curso_codigo': {'curso_codigo', 'codigo_curso', 'codigo curso', 'curso'},
}
ESTADOS = ('valida', 'advertencia', 'ya_asignada', 'omitida', 'error')
ENCABEZADO_PLANTILLA = ['asignatura_codigo', 'asignatura_nombre', 'semestre', 'docente_email', 'curso_codigo',
                        'docente_actual']


class ErrorAsignacion(Exception):
    """Error del archivo completo (estructura, tamaño, formato)."""


# --------------------------------------------------------------- lectura

def _normalizar(texto) -> str:
    from .servicio_supervision import _normalizar as normalizar
    return normalizar(texto).replace('-', '_')


def filas_desde_archivo(archivo) -> list:
    """Lee CSV, XLSX o JSON y devuelve filas {asignatura_codigo, docente_email, curso_codigo, fila}."""
    from .servicio_supervision import _filas_csv, _filas_xlsx

    if archivo.size > MAX_BYTES:
        raise ErrorAsignacion('El archivo supera el máximo de 2 MB.')
    nombre = (archivo.name or '').lower()
    contenido = archivo.read()
    if nombre.endswith('.json'):
        return filas_desde_json(contenido)
    from .servicio_supervision import ErrorSupervision

    if nombre.endswith('.csv') or nombre.endswith('.txt'):
        tabla = _filas_csv(contenido)
    elif nombre.endswith('.xlsx'):
        try:
            tabla = _filas_xlsx(contenido)
        except ErrorSupervision as exc:
            raise ErrorAsignacion(str(exc)) from exc
    else:
        raise ErrorAsignacion('Formato no soportado: sube un archivo .csv, .xlsx o .json.')
    tabla = [f for f in tabla if any(str(c or '').strip() for c in f)]
    if not tabla:
        raise ErrorAsignacion('El archivo no tiene filas.')
    encabezado = [_normalizar(c) for c in tabla[0]]
    columnas = {}
    for campo, alias in COLUMNAS.items():
        for i, titulo in enumerate(encabezado):
            if titulo in {_normalizar(a) for a in alias} and i not in columnas.values():
                columnas[campo] = i
                break
    faltan = [c for c in ('asignatura_codigo', 'docente_email') if c not in columnas]
    if faltan:
        raise ErrorAsignacion(
            'Estructura inválida: faltan las columnas ' + ', '.join(faltan)
            + '. Descarga la plantilla para ver el formato esperado.'
        )
    salida = []
    for n, f in enumerate(tabla[1:], start=2):
        fila = {'fila': n}
        for campo in COLUMNAS:
            i = columnas.get(campo)
            valor = f[i] if i is not None and i < len(f) else ''
            fila[campo] = '' if valor is None else str(valor).strip()
        salida.append(fila)
    if len(salida) > MAX_FILAS:
        raise ErrorAsignacion(f'El archivo trae {len(salida)} filas; el máximo es {MAX_FILAS}.')
    return salida


def filas_desde_json(contenido) -> list:
    try:
        datos = json.loads(contenido.decode('utf-8-sig') if isinstance(contenido, bytes) else contenido)
    except (ValueError, UnicodeDecodeError):
        raise ErrorAsignacion('El JSON no es válido.')
    if isinstance(datos, dict):
        datos = datos.get('asignaciones')
    if not isinstance(datos, list):
        raise ErrorAsignacion('El JSON debe ser una lista de asignaciones o un objeto {"asignaciones": [...]}.')
    if len(datos) > MAX_FILAS:
        raise ErrorAsignacion(f'El archivo trae {len(datos)} filas; el máximo es {MAX_FILAS}.')
    salida = []
    for n, item in enumerate(datos, start=1):
        if not isinstance(item, dict):
            salida.append({'fila': n, 'asignatura_codigo': '', 'docente_email': '', 'curso_codigo': '',
                           'invalida': 'el registro no es un objeto JSON'})
            continue
        salida.append({'fila': n, **{c: str(item.get(c) or '').strip() for c in COLUMNAS}})
    return salida


def huella(filas) -> str:
    canonico = json.dumps([[f.get(c, '') for c in ('fila', *COLUMNAS)] for f in filas], ensure_ascii=False)
    return hashlib.sha256(canonico.encode('utf-8')).hexdigest()


# --------------------------------------------------------------- decisión

def _nombre(usuario) -> str:
    from .servicio_supervision import nombre_completo
    return nombre_completo(usuario)


class Resolutor:
    """Decide el curso para (asignatura, docente). Cachea consultas para un lote."""

    def __init__(self):
        self.User = get_user_model()
        self._docentes = {}
        self._cursos_docente = {}
        self._nuevos = {}  # (docente_id, nombre en minúscula) → nombre del curso a crear en este lote

    def docente(self, email):
        clave = email.lower()
        if clave not in self._docentes:
            self._docentes[clave] = self.User.objects.filter(email__iexact=email).select_related('role').first()
        return self._docentes[clave]

    def cursos(self, docente):
        from apps.examenes.models import Curso

        if docente.id not in self._cursos_docente:
            self._cursos_docente[docente.id] = list(Curso.objects.filter(docente=docente).order_by('id'))
        return self._cursos_docente[docente.id]

    def resolver(self, asignatura, nombre_asignatura, email, curso_codigo='') -> dict:
        """Decisión para una asignatura (existente o por crear) y un docente.

        Devuelve {estado, mensaje, docente, curso, crear_curso, nombre_curso, anterior}.
        """
        from apps.examenes.models import Curso

        d = {'estado': 'error', 'mensaje': '', 'docente': None, 'curso': None, 'crear_curso': False,
             'nombre_curso': '', 'anterior': None}
        try:
            validate_email(email)
        except ValidationError:
            d['mensaje'] = f'Correo inválido: "{email}".'
            return d
        docente = self.docente(email)
        if docente is None:
            d['mensaje'] = f'No existe un usuario con el correo {email}.'
            return d
        if (docente.role.name if docente.role_id else None) != ROL_DOCENTE:
            d['mensaje'] = f'{email} no tiene el rol Docente.'
            return d
        if not docente.is_active:
            d['mensaje'] = f'La cuenta de {email} está inactiva.'
            return d
        d['docente'] = docente
        actual = asignatura.curso_vinculado if asignatura is not None else None
        if actual is not None:
            d['anterior'] = {'curso': actual.nombre, 'codigo': actual.codigo, 'docente_email': actual.docente.email,
                             'docente': _nombre(actual.docente)}

        if curso_codigo:
            curso = Curso.objects.filter(codigo__iexact=curso_codigo).select_related('docente').first()
            if curso is None:
                d['mensaje'] = f'No existe el curso con código {curso_codigo}.'
                return d
            if curso.docente_id != docente.id:
                d['mensaje'] = f'El curso {curso.codigo} pertenece a {curso.docente.email}, no a {email}.'
                return d
        else:
            cursos = self.cursos(docente)
            curso = next((c for c in cursos if actual is not None and c.id == actual.id), None)
            curso = curso or next((c for c in cursos if c.nombre.strip().lower() == nombre_asignatura.strip().lower()),
                                  None)
        if curso is not None and actual is not None and curso.id == actual.id:
            d.update(estado='ya_asignada', curso=curso,
                     mensaje=f'Ya está asignada a {_nombre(docente)} (curso {curso.codigo}).')
            return d

        avisos = []
        if curso is None:
            nombre_curso = nombre_asignatura.strip()[:100]
            llave = (docente.id, nombre_curso.lower())
            d.update(crear_curso=True, nombre_curso=nombre_curso)
            avisos.append(f'El docente no tiene un curso para esta asignatura: se creará el curso "{nombre_curso}".'
                          if llave not in self._nuevos else
                          f'Se usará el curso "{nombre_curso}" que se crea en otra fila de este archivo.')
            self._nuevos.setdefault(llave, nombre_curso)
        else:
            d['curso'] = curso
        if actual is not None:
            avisos.append(f"Reemplaza a {d['anterior']['docente']} ({d['anterior']['docente_email']}).")
        d['estado'] = 'advertencia' if avisos else 'valida'
        d['mensaje'] = ' '.join(avisos) or f'Se asignará a {_nombre(docente)} (curso {curso.codigo}).'
        return d


def planificar(filas, programa=None) -> dict:
    """Valida y decide cada fila sin escribir. `programa` limita a las asignaturas de ese programa."""
    resolutor = Resolutor()
    plan = []
    vistas = {}
    codigos = {f['asignatura_codigo'].lower() for f in filas if f.get('asignatura_codigo')}
    asignaturas = {
        a.codigo.lower(): a for a in AsignaturaMalla.objects.filter(
            codigo__in=[f['asignatura_codigo'] for f in filas if f.get('asignatura_codigo')],
        ).select_related('programa', 'curso_vinculado__docente')
    } if codigos else {}
    # `codigo__in` distingue mayúsculas: se completa sin distinguirlas.
    for codigo in codigos - set(asignaturas):
        a = AsignaturaMalla.objects.filter(codigo__iexact=codigo).select_related(
            'programa', 'curso_vinculado__docente').first()
        if a is not None:
            asignaturas[codigo] = a

    for f in filas:
        salida = {'fila': f['fila'], 'asignatura_codigo': f.get('asignatura_codigo', ''),
                  'docente_email': f.get('docente_email', ''), 'curso_codigo': f.get('curso_codigo', ''),
                  'asignatura': None, 'docente': None, 'curso': None, 'anterior': None, 'crear_curso': False,
                  'estado': 'error', 'mensaje': '', '_decision': None}
        plan.append(salida)
        codigo, email = salida['asignatura_codigo'], salida['docente_email']
        if f.get('invalida'):
            salida['mensaje'] = f['invalida'].capitalize() + '.'
            continue
        if not codigo:
            salida['mensaje'] = 'Falta el código de la asignatura.' if email else 'Fila vacía.'
            continue
        asignatura = asignaturas.get(codigo.lower())
        if asignatura is None:
            salida['mensaje'] = f'No existe la asignatura con código {codigo}.'
            continue
        salida['asignatura'] = {'id': asignatura.id, 'codigo': asignatura.codigo, 'nombre': asignatura.nombre,
                                'programa': asignatura.programa.codigo}
        if programa is not None and asignatura.programa_id != programa.id:
            salida['mensaje'] = (f'La asignatura {asignatura.codigo} pertenece al programa '
                                 f'{asignatura.programa.codigo}, no a {programa.codigo}.')
            continue
        if not asignatura.activo:
            salida['mensaje'] = f'La asignatura {asignatura.codigo} está inactiva.'
            continue
        llave = asignatura.codigo.lower()
        if llave in vistas:
            salida['mensaje'] = f'Asignatura repetida en el archivo (ya aparece en la fila {vistas[llave]}).'
            continue
        vistas[llave] = f['fila']
        if not email:
            salida.update(estado='omitida', mensaje='Sin docente en la fila: la asignatura no cambia.')
            continue
        d = resolutor.resolver(asignatura, asignatura.nombre, email, salida['curso_codigo'])
        salida.update(estado=d['estado'], mensaje=d['mensaje'], anterior=d['anterior'], crear_curso=d['crear_curso'])
        if d['docente'] is not None:
            salida['docente'] = {'email': d['docente'].email, 'nombre': _nombre(d['docente'])}
        if d['curso'] is not None:
            salida['curso'] = {'codigo': d['curso'].codigo, 'nombre': d['curso'].nombre}
        elif d['crear_curso']:
            salida['curso'] = {'codigo': None, 'nombre': d['nombre_curso']}
        if d['estado'] in ('valida', 'advertencia'):
            salida['_decision'] = (asignatura, d)

    resumen = {e: sum(1 for p in plan if p['estado'] == e) for e in ESTADOS}
    resumen['total'] = len(plan)
    resumen['cursos_nuevos'] = sum(1 for p in plan if p['crear_curso'] and p['_decision'])
    resumen['cambios_docente'] = sum(1 for p in plan if p['anterior'] and p['_decision'])
    return {'filas': plan, 'resumen': resumen}


def aplicar_decision(asignatura, d, creados: dict) -> 'object':
    """Vincula el curso decidido. `creados` evita crear dos veces el mismo curso en un lote."""
    from apps.examenes.models import Curso

    curso = d['curso']
    if d['crear_curso']:
        llave = (d['docente'].id, d['nombre_curso'].lower())
        curso = creados.get(llave)
        if curso is None:
            curso = Curso.objects.create(
                nombre=d['nombre_curso'], docente=d['docente'],
                descripcion=f'Creado por asignación masiva de docentes para la asignatura {asignatura.codigo}.',
            )
            creados[llave] = curso
    asignatura.curso_vinculado = curso
    asignatura.save(update_fields=['curso_vinculado'])
    return curso


def aplicar(plan) -> dict:
    """Escribe todas las filas válidas y con advertencia, o ninguna."""
    creados = {}
    with transaction.atomic():
        for fila in plan['filas']:
            if fila['_decision'] is None:
                continue
            asignatura, d = fila['_decision']
            curso = aplicar_decision(asignatura, d, creados)
            fila['curso'] = {'codigo': curso.codigo, 'nombre': curso.nombre}
            fila['aplicada'] = True
    return {'asignadas': sum(1 for f in plan['filas'] if f.get('aplicada')), 'cursos_creados': len(creados)}


def publico(plan) -> list:
    """Filas sin los objetos internos, para la respuesta."""
    return [{k: v for k, v in f.items() if k != '_decision'} for f in plan['filas']]


# --------------------------------------------------------------- plantilla

def _filas_plantilla(programa) -> list:
    asignaturas = (AsignaturaMalla.objects.filter(programa=programa, activo=True)
                   .select_related('semestre', 'curso_vinculado__docente').order_by('semestre__numero', 'nombre'))
    return [[a.codigo, a.nombre, a.semestre.numero if a.semestre_id else '',
             a.curso_vinculado.docente.email if a.curso_vinculado_id else '',
             a.curso_vinculado.codigo if a.curso_vinculado_id else '',
             _nombre(a.curso_vinculado.docente) if a.curso_vinculado_id else 'Sin docente']
            for a in asignaturas]


def plantilla_csv(programa) -> bytes:
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(ENCABEZADO_PLANTILLA)
    escritor.writerows(_filas_plantilla(programa))
    return ('﻿' + salida.getvalue()).encode('utf-8')


def plantilla_xlsx(programa) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    User = get_user_model()
    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Asignaciones'
    hoja.append(ENCABEZADO_PLANTILLA)
    for c in hoja[1]:
        c.font, c.fill = Font(bold=True, color='FFFFFF'), PatternFill('solid', fgColor='1F4E8C')
    filas = _filas_plantilla(programa)
    for f in filas:
        hoja.append(f)
    for col, ancho in zip('ABCDEF', (18, 50, 10, 34, 14, 34)):
        hoja.column_dimensions[col].width = ancho
    hoja.freeze_panes = 'A2'
    hoja.auto_filter.ref = f'A1:F{len(filas) + 1}'

    docentes = libro.create_sheet('Docentes')
    docentes.append(['docente_email', 'nombre', 'cursos (código · nombre)'])
    for c in docentes[1]:
        c.font = Font(bold=True)
    lista = (User.objects.filter(role__name=ROL_DOCENTE, is_active=True)
             .prefetch_related('cursos').order_by('email'))
    for u in lista:
        docentes.append([u.email, _nombre(u), '; '.join(f'{c.codigo} · {c.nombre}' for c in u.cursos.all())])
    docentes.column_dimensions['A'].width, docentes.column_dimensions['B'].width = 34, 34
    docentes.column_dimensions['C'].width = 70
    if lista:
        validacion = DataValidation(type='list', formula1=f'=Docentes!$A$2:$A${len(lista) + 1}', allow_blank=True,
                                    showErrorMessage=False)
        hoja.add_data_validation(validacion)
        validacion.add(f'D2:D{max(len(filas), 1) + 500}')

    ayuda = libro.create_sheet('Instrucciones')
    for linea in [
        f'Programa: {programa.codigo} · {programa.nombre}',
        '1. Escribe en "docente_email" el correo del docente de cada asignatura (lista en la hoja Docentes).',
        '2. "curso_codigo" es opcional: úsalo si el docente tiene varios cursos y quieres elegir uno.',
        '   Sin código se usa el curso del docente que ya implementa la asignatura o uno con el mismo nombre;',
        '   si no tiene ninguno, se creará un curso con el nombre de la asignatura (se avisa antes de confirmar).',
        '3. Deja "docente_email" vacío para no cambiar esa asignatura.',
        '4. asignatura_nombre, semestre y docente_actual son informativas: no se leen al cargar.',
        '5. Sube el archivo, revisa la vista previa y confirma. Se aplica todo o nada.',
    ]:
        ayuda.append([linea])
    ayuda['A1'].font = Font(bold=True)
    ayuda.column_dimensions['A'].width = 110
    for fila in ayuda.iter_rows():
        fila[0].alignment = Alignment(wrap_text=False)

    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()
