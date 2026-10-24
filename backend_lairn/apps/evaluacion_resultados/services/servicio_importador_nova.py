"""
Importador idempotente de programas/asignaturas/usuarios (HU-03.1 / 03.2
en modo compatible). La fuente puede ser una URL, un archivo o JSON pegado:
este servicio solo recibe el JSON ya parseado.

Contrato JSON aceptado (el del correo de TI):
{
  "programas": [{codigo, nombre, modalidad?, sede?, duracion?, vigencia?,
                 external_id?, semestres?: [1,2,...]}],
  "asignaturas": [{codigo, nombre, creditos?, intensidad?, tipo?,
                    programa_codigo, semestre?, external_id?}],
  "usuarios": [{email, ...}]
}

Flujo en dos fases para que la vista previa diga exactamente lo que hará
la importación real:
  1. `_planificar`: valida cada registro (tipos, rangos, duplicados en el
     lote, conflictos con la BD) y decide crear/actualizar/rechazar/omitir.
     No escribe nada.
  2. Solo en `modo='real'`: aplica el plan dentro de una transacción. Si
     algo falla no queda nada a medias y se reporta el fallo.

Reglas de negocio que preserva:
  - Clave natural `codigo`, comparada sin distinguir mayúsculas (igual que
    el alta manual), así nunca duplica aunque se ejecute N veces.
  - En una actualización no se tocan `activo`, `estado_revision` ni
    `origen`: un programa desactivado por el administrador sigue inactivo.
  - Una asignatura existente que pertenece a otro programa se rechaza en
    lugar de moverse en silencio.
  - Usuarios: nunca se crean ni modifican cuentas desde aquí; solo se
    informa si existen (alta pendiente por TI).

`huella` (SHA-256 del JSON canónico) permite confirmar que se importa lo
mismo que se revisó en la vista previa.
"""

import hashlib
import json
import logging
from datetime import date

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    OpcionesEstadoRevision,
    OpcionesOrigen,
    OpcionesTipoAsignatura,
    ProgramaAcademico,
    SemestrePrograma,
)
from .servicio_trazabilidad import registrar_sincronizacion

logger = logging.getLogger(__name__)

MAX_REGISTROS = 5000
MAX_DETALLE_RESPUESTA = 500
DURACION_MAXIMA = 14  # mismo rango que el alta manual de programas
CREDITOS_MAXIMOS = 20  # mismo rango que el alta manual de asignaturas

# Campo del modelo -> clave en el JSON de origen.
CAMPOS_PROGRAMA = {
    'nombre': 'nombre', 'modalidad': 'modalidad', 'sede': 'sede',
    'duracion_semestres': 'duracion', 'fecha_vigencia': 'vigencia',
}
CAMPOS_ASIGNATURA = {
    'nombre': 'nombre', 'creditos': 'creditos',
    'intensidad_horaria': 'intensidad', 'tipo': 'tipo',
}


class ErrorImportacion(Exception):
    """Error presentable al administrador; `estado` es el HTTP sugerido."""

    def __init__(self, mensaje: str, estado: int = 400):
        super().__init__(mensaje)
        self.estado = estado


def calcular_huella(payload) -> str:
    canonico = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(canonico.encode('utf-8')).hexdigest()


# --- Normalización de campos -------------------------------------------------

def _texto(item: dict, campo: str, *, max_len: int, requerido: bool = False, defecto: str = '') -> str:
    valor = item.get(campo)
    if valor is None or valor == '':
        if requerido:
            raise ValueError(f'falta el campo "{campo}"')
        return defecto
    if isinstance(valor, bool) or not isinstance(valor, (str, int)):
        raise ValueError(f'"{campo}" debe ser texto')
    texto = str(valor).strip()
    if requerido and not texto:
        raise ValueError(f'falta el campo "{campo}"')
    if len(texto) > max_len:
        raise ValueError(f'"{campo}" supera {max_len} caracteres')
    return texto or defecto


def _entero(item: dict, campo: str, *, minimo: int, maximo: int, defecto=None):
    valor = item.get(campo)
    if valor is None or valor == '':
        return defecto
    if isinstance(valor, bool):
        raise ValueError(f'"{campo}" debe ser un número entero')
    if isinstance(valor, str) and valor.strip().isdigit():
        valor = int(valor.strip())
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    if not isinstance(valor, int):
        raise ValueError(f'"{campo}" debe ser un número entero')
    if valor < minimo or valor > maximo:
        raise ValueError(f'"{campo}" debe estar entre {minimo} y {maximo}')
    return valor


def _fecha(item: dict, campo: str):
    valor = item.get(campo)
    if valor in (None, ''):
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        raise ValueError(f'"{campo}" debe ser una fecha AAAA-MM-DD')


def _lista(payload: dict, clave: str) -> list:
    valor = payload.get(clave, [])
    if valor is None:
        return []
    if not isinstance(valor, list):
        raise ErrorImportacion(f'"{clave}" debe ser una lista de registros.')
    return valor


# --- Fase 1: planificar (sin escrituras) -------------------------------------

def _fila(entidad, clave, nombre, accion, motivo=''):
    return {'entidad': entidad, 'clave': clave, 'nombre': nombre, 'accion': accion, 'motivo': motivo}


def _planificar(payload) -> dict:
    if not isinstance(payload, dict):
        raise ErrorImportacion(
            'El JSON debe ser un objeto con las listas "programas", "asignaturas" y/o "usuarios".'
        )
    programas = _lista(payload, 'programas')
    asignaturas = _lista(payload, 'asignaturas')
    usuarios = _lista(payload, 'usuarios')
    total = len(programas) + len(asignaturas) + len(usuarios)
    if total == 0:
        raise ErrorImportacion(
            'El JSON no contiene registros: se esperaban "programas", "asignaturas" o "usuarios".'
        )
    if total > MAX_REGISTROS:
        raise ErrorImportacion(f'El JSON trae {total} registros; el máximo por importación es {MAX_REGISTROS}.')

    filas: list = []
    plan_programas: list = []
    plan_asignaturas: list = []
    # codigo en minúscula -> ('nuevo'|ProgramaAcademico, duracion) de los válidos del lote
    programas_lote: dict = {}
    rechazados_lote: set = set()

    for i, item in enumerate(programas, start=1):
        if not isinstance(item, dict):
            filas.append(_fila('programa', f'#{i}', '', 'rechazar', 'el registro no es un objeto JSON'))
            continue
        clave = str(item.get('codigo') or f'#{i}')[:30]
        existente = None
        try:
            codigo = _texto(item, 'codigo', max_len=30, requerido=True)
            existente = ProgramaAcademico.objects.filter(codigo__iexact=codigo).first()
            datos = {
                'nombre': _texto(item, 'nombre', max_len=200, requerido=True),
                'modalidad': _texto(item, 'modalidad', max_len=30, defecto='Presencial'),
                'sede': _texto(item, 'sede', max_len=100, defecto='Principal'),
                'duracion_semestres': _entero(item, 'duracion', minimo=1, maximo=DURACION_MAXIMA, defecto=8),
                'fecha_vigencia': _fecha(item, 'vigencia'),
            }
            # Al actualizar, un campo ausente en el JSON conserva su valor actual
            # (los defaults solo aplican al crear).
            if existente is not None:
                datos = {campo: valor for campo, valor in datos.items()
                         if item.get(CAMPOS_PROGRAMA[campo]) not in (None, '')}
            duracion = datos.get('duracion_semestres') or (existente.duracion_semestres if existente else 8)
            external_id = _texto(item, 'external_id', max_len=100) or None
            semestres_crudos = item.get('semestres') or []
            if not isinstance(semestres_crudos, list):
                raise ValueError('"semestres" debe ser una lista de números')
            semestres = sorted({
                _entero({'semestre': s}, 'semestre', minimo=1, maximo=duracion)
                for s in semestres_crudos
            })
        except ValueError as exc:
            filas.append(_fila('programa', clave, str(item.get('nombre') or '')[:200], 'rechazar', str(exc)))
            rechazados_lote.add(clave.lower())
            continue
        llave = codigo.lower()
        if llave in programas_lote:
            filas.append(_fila('programa', codigo, datos['nombre'], 'rechazar', 'código repetido dentro del archivo'))
            continue
        accion = 'actualizar' if existente else 'crear'
        programas_lote[llave] = (existente or 'nuevo', duracion)
        plan_programas.append({
            'codigo': existente.codigo if existente else codigo,
            'existente': existente, 'datos': datos, 'external_id': external_id,
            'semestres': semestres, 'crudo': item,
        })
        filas.append(_fila('programa', codigo, datos['nombre'], accion))

    vistas_asignatura: set = set()
    for i, item in enumerate(asignaturas, start=1):
        if not isinstance(item, dict):
            filas.append(_fila('asignatura', f'#{i}', '', 'rechazar', 'el registro no es un objeto JSON'))
            continue
        clave = str(item.get('codigo') or f'#{i}')[:30]
        try:
            codigo = _texto(item, 'codigo', max_len=30, requerido=True)
            prog_codigo = _texto(item, 'programa_codigo', max_len=30, requerido=True)
            tipo = _texto(item, 'tipo', max_len=20, defecto=OpcionesTipoAsignatura.OBLIGATORIA).lower()
            if tipo not in OpcionesTipoAsignatura.values:
                raise ValueError(f'"tipo" debe ser uno de: {", ".join(OpcionesTipoAsignatura.values)}')
            datos = {
                'nombre': _texto(item, 'nombre', max_len=200, requerido=True),
                'creditos': _entero(item, 'creditos', minimo=0, maximo=CREDITOS_MAXIMOS, defecto=3),
                'intensidad_horaria': _entero(item, 'intensidad', minimo=0, maximo=200, defecto=0),
                'tipo': tipo,
            }
            numero_semestre = _entero(item, 'semestre', minimo=1, maximo=DURACION_MAXIMA)
            external_id = _texto(item, 'external_id', max_len=100) or None
        except ValueError as exc:
            filas.append(_fila('asignatura', clave, str(item.get('nombre') or '')[:200], 'rechazar', str(exc)))
            continue
        llave = codigo.lower()
        if llave in vistas_asignatura:
            filas.append(_fila('asignatura', codigo, datos['nombre'], 'rechazar', 'código repetido dentro del archivo'))
            continue
        vistas_asignatura.add(llave)

        destino = programas_lote.get(prog_codigo.lower())
        if destino is None and prog_codigo.lower() in rechazados_lote:
            filas.append(_fila('asignatura', codigo, datos['nombre'], 'rechazar',
                               f'su programa {prog_codigo} fue rechazado'))
            continue
        if destino is None:
            programa_bd = ProgramaAcademico.objects.filter(codigo__iexact=prog_codigo).first()
            if programa_bd is None:
                filas.append(_fila('asignatura', codigo, datos['nombre'], 'rechazar',
                                   f'el programa {prog_codigo} no existe'))
                continue
            destino = (programa_bd, programa_bd.duracion_semestres)
        programa, duracion = destino
        if numero_semestre and numero_semestre > duracion:
            filas.append(_fila('asignatura', codigo, datos['nombre'], 'rechazar',
                               f'el semestre {numero_semestre} supera la duración del programa ({duracion})'))
            continue
        existente = AsignaturaMalla.objects.filter(codigo__iexact=codigo).select_related('programa').first()
        if existente and (programa == 'nuevo' or existente.programa_id != programa.pk):
            filas.append(_fila('asignatura', codigo, datos['nombre'], 'rechazar',
                               f'ya existe en el programa {existente.programa.codigo}; no se mueve automáticamente'))
            continue
        if existente is not None:
            datos = {campo: valor for campo, valor in datos.items()
                     if item.get(CAMPOS_ASIGNATURA[campo]) not in (None, '')}
        plan_asignaturas.append({
            'codigo': existente.codigo if existente else codigo,
            'programa_codigo': prog_codigo.lower(), 'existente': existente, 'datos': datos,
            'semestre': numero_semestre, 'external_id': external_id, 'crudo': item,
        })
        filas.append(_fila('asignatura', codigo, datos['nombre'], 'actualizar' if existente else 'crear'))

    User = get_user_model()
    vistos_usuario: set = set()
    for i, item in enumerate(usuarios, start=1):
        email = str(item.get('email') or '').strip().lower() if isinstance(item, dict) else ''
        if not email or '@' not in email or len(email) > 254:
            filas.append(_fila('usuario', email or f'#{i}', '', 'rechazar', 'falta un email válido'))
            continue
        if email in vistos_usuario:
            filas.append(_fila('usuario', email, '', 'rechazar', 'email repetido dentro del archivo'))
            continue
        vistos_usuario.add(email)
        nombre = f"{item.get('nombres') or ''} {item.get('apellidos') or ''}".strip()[:200]
        if User.objects.filter(email__iexact=email).exists():
            filas.append(_fila('usuario', email, nombre, 'sin_cambios',
                               'ya registrado; las cuentas no se modifican desde la importación'))
        else:
            filas.append(_fila('usuario', email, nombre, 'omitir', 'no existe en PseudoTutor; alta pendiente por TI'))

    return {
        'total': total, 'filas': filas,
        'programas': plan_programas, 'asignaturas': plan_asignaturas,
    }


# --- Fase 2: aplicar (solo modo real) ----------------------------------------

def _aplicar(plan: dict) -> None:
    programas_obj: dict = {}
    for p in plan['programas']:
        datos = {**p['datos'], 'datos_origen': p['crudo']}
        if p['external_id']:
            datos['external_id'] = p['external_id']
        if p['existente'] is not None:
            programa = p['existente']
            for campo, valor in datos.items():
                setattr(programa, campo, valor)
            programa.save()
        else:
            programa = ProgramaAcademico.objects.create(
                codigo=p['codigo'], origen=OpcionesOrigen.API_NOVA,
                estado_revision=OpcionesEstadoRevision.APROBADO, activo=True, **datos,
            )
        programas_obj[p['codigo'].lower()] = programa
        for numero in p['semestres']:
            SemestrePrograma.objects.get_or_create(
                programa=programa, numero=numero,
                defaults={'origen': OpcionesOrigen.API_NOVA, 'estado_revision': OpcionesEstadoRevision.APROBADO},
            )

    for a in plan['asignaturas']:
        programa = programas_obj.get(a['programa_codigo']) or ProgramaAcademico.objects.get(
            codigo__iexact=a['programa_codigo'],
        )
        semestre = None
        if a['semestre']:
            semestre, _ = SemestrePrograma.objects.get_or_create(
                programa=programa, numero=a['semestre'],
                defaults={'origen': OpcionesOrigen.API_NOVA, 'estado_revision': OpcionesEstadoRevision.APROBADO},
            )
        datos = {**a['datos'], 'datos_origen': a['crudo']}
        # Sin semestre en el JSON, una asignatura existente conserva su ubicación.
        if semestre is not None or a['existente'] is None:
            datos['semestre'] = semestre
        if a['external_id']:
            datos['external_id'] = a['external_id']
        if a['existente'] is not None:
            asignatura = a['existente']
            for campo, valor in datos.items():
                setattr(asignatura, campo, valor)
            asignatura.save()
        else:
            AsignaturaMalla.objects.create(
                codigo=a['codigo'], programa=programa, origen=OpcionesOrigen.API_NOVA,
                estado_revision=OpcionesEstadoRevision.APROBADO, activo=True, **datos,
            )


def importar_programas_json(
    payload,
    *,
    modo: str = 'simulacro',
    ejecutado_por=None,
    origen: str = 'api_nova_json',
    huella_esperada: str | None = None,
) -> dict:
    huella = calcular_huella(payload)
    if huella_esperada and huella_esperada != huella:
        raise ErrorImportacion(
            'Los datos de la fuente cambiaron desde la validación. Vuelve a validar antes de importar.',
            estado=409,
        )
    plan = _planificar(payload)
    filas = plan['filas']
    conteo = {a: sum(1 for f in filas if f['accion'] == a)
              for a in ('crear', 'actualizar', 'sin_cambios', 'omitir', 'rechazar')}
    errores = [
        f"{f['entidad'].capitalize()} {f['clave']}: {f['motivo']}"
        for f in filas if f['accion'] in ('rechazar', 'omitir')
    ]

    if modo == 'real':
        try:
            with transaction.atomic():
                _aplicar(plan)
        except Exception:
            # El detalle técnico va al log, nunca a la respuesta.
            logger.exception('Fallo al aplicar importación JSON (origen=%s)', origen)
            registrar_sincronizacion(
                origen=origen, entidad='programas/asignaturas/usuarios', modo='real_fallido',
                total_recibidos=plan['total'],
                errores=['No se guardó ningún cambio: falló la escritura en la base de datos.'],
                ejecutado_por=ejecutado_por,
            )
            raise ErrorImportacion(
                'No se guardó ningún cambio: ocurrió un error al escribir en la base de datos. '
                'Intenta de nuevo o contacta a soporte.',
                estado=500,
            )

    registro = registrar_sincronizacion(
        origen=origen,
        entidad='programas/asignaturas/usuarios',
        modo=modo,
        total_recibidos=plan['total'],
        creados=conteo['crear'],
        actualizados=conteo['actualizar'],
        omitidos=conteo['omitir'] + conteo['rechazar'],
        errores=errores[:50],
        ejecutado_por=ejecutado_por,
    )
    return {
        'registro_id': registro.id,
        'modo': modo,
        'origen': origen,
        'huella': huella,
        'total_recibidos': plan['total'],
        'creados': conteo['crear'],
        'actualizados': conteo['actualizar'],
        'sin_cambios': conteo['sin_cambios'],
        'omitidos': conteo['omitir'],
        'rechazados': conteo['rechazar'],
        'errores': errores[:50],
        'registros': filas[:MAX_DETALLE_RESPUESTA],
        'registros_truncados': len(filas) > MAX_DETALLE_RESPUESTA,
    }
