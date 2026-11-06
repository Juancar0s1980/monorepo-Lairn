"""
Supervisión en sala, asistencia y convocatoria masiva de la evaluación formal (ADR-009).

- Supervisor: docente con al menos un curso Lairn (`examenes.Curso`). Lo
  asigna el Coordinador o el Administrador; activa el control de asistencia.
- Llamado a lista: el supervisor marca presente / tarde / ausente / excusa
  desde 2 h antes de la apertura hasta el cierre. Solo presente y tarde
  habilitan iniciar. No se puede ausentar ni excusar a quien ya inició.
- Seguimiento en vivo: conteos y filas por convocado con su asistencia y su
  intento; la nota solo la ve el Coordinador/Administrador.
- Integridad (ADR-010): cada fila trae el estado de integridad del intento,
  sus incidentes y resoluciones; los conteos suman advertidos, suspendidos y
  anulados por fraude.
- Cargue masivo: lista de correos (CSV, Excel o JSON). Quien ya está
  convocado (por curso o por cargue) queda igual; solo se agrega a quien
  falta y existe como Estudiante. No crea cuentas (eso es HU-03.1, TI).
  ADR-012: el archivo puede traer nombre, programa, semestre y código; se
  comparan con la cuenta y el `PerfilAcademico` y solo se INFORMAN las
  diferencias (nunca se sobrescribe nada).
"""

import csv
import io
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Count
from django.db.models.functions import Lower
from django.utils import timezone

from apps.evaluacion_resultados.models import (
    AsistenciaEvaluacion,
    ConvocadoEvaluacion,
    OpcionesEstadoAsistencia,
    OpcionesTipoExcusa,
)
from apps.evaluacion_resultados.services.servicio_presentacion import (
    cerrar_si_vencido,
    origenes_convocatoria,
)

MARGEN_LLAMADO = timedelta(hours=2)
MAX_FILAS_CARGUE = 2000
MAX_BYTES_CARGUE = 2 * 1024 * 1024
COLUMNAS_CORREO = {'correo', 'email', 'correo electronico', 'correo electrónico', 'e-mail'}
# Estados de la vista previa (ADR-012): agregar = válido; no_encontrado = no existe la cuenta;
# invalido = formato inválido. Las claves se conservan por compatibilidad con ADR-009.
ESTADOS_CARGUE = ['agregar', 'ya_convocado', 'no_encontrado', 'no_es_estudiante', 'duplicado_en_archivo', 'invalido',
                  'campo_obligatorio_faltante']
# Validación global del Administrador (sin evaluación): existe = la cuenta ya existe y es de estudiante.
ESTADOS_VALIDACION = ['existe', 'no_encontrado', 'no_es_estudiante', 'duplicado_en_archivo', 'invalido',
                      'campo_obligatorio_faltante']


class ErrorSupervision(Exception):
    def __init__(self, mensaje, status=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status


def nombre_completo(usuario) -> str:
    partes = [usuario.first_name, usuario.second_name, usuario.first_last_name, usuario.second_last_name]
    return ' '.join(p for p in partes if p) or usuario.email


# ---------------------------------------------------------------- supervisores

def docentes_con_cursos():
    from apps.users.models import User

    return (
        User.objects.filter(role__name='Docente', is_active=True, cursos__isnull=False)
        .annotate(total_cursos=Count('cursos', distinct=True))
        .order_by('first_name', 'first_last_name')
    )


def es_docente_con_cursos(usuario_id) -> bool:
    return docentes_con_cursos().filter(id=usuario_id).exists()


# ---------------------------------------------------------------- seguimiento

def _fila_intento(intento, con_nota, total_preguntas):
    from apps.evaluacion_resultados.services.servicio_integridad import datos_integridad

    if intento is None:
        return None
    datos = {
        'integridad': datos_integridad(intento),
        'estado': 'enviado' if intento.enviado else 'en_curso',
        'iniciado_en': intento.iniciado_en, 'vence_en': intento.vence_en,
        'respondidas': len(intento.respuestas), 'total': intento.total or total_preguntas,
        'enviado_en': intento.enviado_en, 'envio_automatico': intento.envio_automatico,
    }
    if con_nota:
        datos['nota'] = intento.nota
        datos['aciertos'] = intento.aciertos
    return datos


def ventana_llamado(evaluacion):
    return evaluacion.fecha_inicio - MARGEN_LLAMADO, evaluacion.fecha_fin


def resumen_evaluacion(evaluacion) -> dict:
    desde, hasta = ventana_llamado(evaluacion)
    momento = evaluacion.momento
    return {
        'id': evaluacion.id, 'nombre': evaluacion.nombre, 'tipo': evaluacion.tipo, 'estado': evaluacion.estado,
        'momento': momento.nombre,
        'programa': f'{momento.programa.codigo} · {momento.programa.nombre}',
        'fecha_inicio': evaluacion.fecha_inicio, 'fecha_fin': evaluacion.fecha_fin,
        'duracion_minutos': evaluacion.duracion_minutos, 'total_preguntas': evaluacion.items.count(),
        'supervisor': evaluacion.supervisor_id,
        'supervisor_nombre': nombre_completo(evaluacion.supervisor) if evaluacion.supervisor_id else None,
        'requiere_asistencia': bool(evaluacion.supervisor_id),
        'llamado_desde': desde, 'llamado_hasta': hasta,
    }


def seguimiento(evaluacion, *, con_nota: bool) -> dict:
    """Estado en vivo de todos los convocados. Cierra antes los intentos vencidos."""
    from apps.users.models import User

    ahora = timezone.now()
    origenes = origenes_convocatoria(evaluacion)
    estudiantes = User.objects.filter(id__in=origenes.keys(), role__name='Estudiante').order_by(
        'first_last_name', 'first_name', 'email',
    )
    asistencias = {a.estudiante_id: a for a in evaluacion.asistencias.all()}
    intentos = {
        i.estudiante_id: cerrar_si_vencido(i, ahora)
        for i in evaluacion.intentos.prefetch_related('incidentes', 'resoluciones__resuelto_por')
    }
    total_preguntas = evaluacion.items.count()

    conteos = dict.fromkeys(
        ['convocados', 'presentes', 'tarde', 'ausentes', 'excusa', 'sin_llamar', 'en_curso', 'enviados',
         'sin_iniciar', 'advertidos', 'suspendidos', 'anulados'], 0,
    )
    clave_integridad = {'advertido': 'advertidos', 'suspendido': 'suspendidos', 'anulado_fraude': 'anulados'}
    clave_asistencia = {
        OpcionesEstadoAsistencia.PRESENTE: 'presentes', OpcionesEstadoAsistencia.TARDE: 'tarde',
        OpcionesEstadoAsistencia.AUSENTE: 'ausentes', OpcionesEstadoAsistencia.EXCUSA: 'excusa',
    }
    filas = []
    for est in estudiantes:
        asis = asistencias.get(est.id)
        intento = intentos.get(est.id)
        conteos['convocados'] += 1
        conteos[clave_asistencia[asis.estado] if asis else 'sin_llamar'] += 1
        if intento is not None and intento.integridad in clave_integridad:
            conteos[clave_integridad[intento.integridad]] += 1
        if intento is None:
            conteos['sin_iniciar'] += 1
        elif intento.enviado:
            conteos['enviados'] += 1
        else:
            conteos['en_curso'] += 1
        filas.append({
            'estudiante': est.id, 'nombre': nombre_completo(est), 'email': est.email,
            'origen': origenes[est.id],
            'asistencia': None if asis is None else {
                'estado': asis.estado, 'tipo_excusa': asis.tipo_excusa or None,
                'observacion': asis.observacion, 'llegada_en': asis.llegada_en,
                'actualizado_en': asis.actualizado_en,
            },
            'intento': _fila_intento(intento, con_nota, total_preguntas),
        })
    return {
        'evaluacion': resumen_evaluacion(evaluacion), 'ahora_servidor': ahora,
        'conteos': conteos, 'filas': filas,
    }


# ---------------------------------------------------------------- asistencia

def validar_ventana_llamado(evaluacion, ahora=None):
    ahora = ahora or timezone.now()
    desde, hasta = ventana_llamado(evaluacion)
    if not desde <= ahora <= hasta:
        raise ErrorSupervision('El llamado a lista solo se puede hacer desde 2 horas antes de la apertura hasta el cierre.')


def registrar_asistencia(evaluacion, estudiante_id, estado, *, tipo_excusa='', observacion='', por,
                         ahora=None, convocados=None):
    """Crea o actualiza el registro de asistencia. Lanza `ErrorSupervision`."""
    ahora = ahora or timezone.now()
    validar_ventana_llamado(evaluacion, ahora)
    if estado not in OpcionesEstadoAsistencia.values:
        raise ErrorSupervision('Estado de asistencia no válido.')
    observacion = (observacion or '').strip()
    if len(observacion) > 300:
        raise ErrorSupervision('La observación admite máximo 300 caracteres.')
    if estado == OpcionesEstadoAsistencia.EXCUSA:
        if tipo_excusa not in OpcionesTipoExcusa.values:
            raise ErrorSupervision('Indica el tipo de excusa (permiso médico, calamidad, institucional u otra).')
    else:
        tipo_excusa = ''
    convocados = convocados if convocados is not None else origenes_convocatoria(evaluacion)
    if isinstance(estudiante_id, bool) or not isinstance(estudiante_id, int) or estudiante_id not in convocados:
        raise ErrorSupervision('El estudiante no está convocado a esta evaluación.')
    if estado in (OpcionesEstadoAsistencia.AUSENTE, OpcionesEstadoAsistencia.EXCUSA) and \
            evaluacion.intentos.filter(estudiante_id=estudiante_id).exists():
        raise ErrorSupervision('El estudiante ya inició la evaluación: no se puede marcar ausente ni con excusa.', 409)

    registro = AsistenciaEvaluacion.objects.filter(evaluacion=evaluacion, estudiante_id=estudiante_id).first()
    if registro is None:
        registro = AsistenciaEvaluacion(evaluacion=evaluacion, estudiante_id=estudiante_id)
    registro.estado = estado
    registro.tipo_excusa = tipo_excusa
    registro.observacion = observacion
    registro.registrado_por = por
    if estado in (OpcionesEstadoAsistencia.PRESENTE, OpcionesEstadoAsistencia.TARDE):
        registro.llegada_en = registro.llegada_en or ahora
    else:
        registro.llegada_en = None
    registro.save()
    return registro


# ---------------------------------------------------------------- cargue masivo

def _filas_csv(contenido: bytes):
    try:
        texto = contenido.decode('utf-8-sig')
    except UnicodeDecodeError:
        texto = contenido.decode('latin-1')
    try:
        dialecto = csv.Sniffer().sniff(texto[:2048], delimiters=',;\t')
    except csv.Error:
        dialecto = csv.excel
    return [list(f) for f in csv.reader(io.StringIO(texto), dialecto)]


def _filas_xlsx(contenido: bytes):
    from openpyxl import load_workbook

    try:
        libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
        hoja = libro.worksheets[0]
        filas = []
        for fila in hoja.iter_rows(values_only=True):
            filas.append(['' if c is None else str(c) for c in fila])
            if len(filas) > MAX_FILAS_CARGUE + 1:
                break
        libro.close()
    except Exception as exc:  # archivo corrupto o no es Excel
        raise ErrorSupervision('No se pudo leer el archivo de Excel.') from exc
    return filas


# Encabezados reconocidos (sin tildes, en minúscula). Solo el correo es obligatorio.
COLUMNAS = {
    'correo': {'correo', 'email', 'correo electronico', 'e-mail', 'correo institucional'},
    'nombre': {'nombre', 'nombres', 'nombre completo', 'estudiante', 'apellidos y nombres'},
    'programa': {'programa', 'programa academico', 'codigo programa'},
    'semestre': {'semestre', 'semestre actual'},
    'codigo': {'codigo', 'codigo estudiantil', 'codigo estudiante', 'matricula', 'codigo de matricula'},
}


def _normalizar(texto) -> str:
    import unicodedata

    texto = unicodedata.normalize('NFD', str(texto or '').strip().lower())
    return ' '.join(''.join(c for c in texto if unicodedata.category(c) != 'Mn').split())


def _leer_tabla(archivo) -> list:
    if archivo.size > MAX_BYTES_CARGUE:
        raise ErrorSupervision('El archivo supera el máximo de 2 MB.')
    nombre = (archivo.name or '').lower()
    contenido = archivo.read()
    if nombre.endswith('.csv') or nombre.endswith('.txt'):
        filas = _filas_csv(contenido)
    elif nombre.endswith('.xlsx'):
        filas = _filas_xlsx(contenido)
    else:
        raise ErrorSupervision('Formato no soportado: sube un archivo .csv o .xlsx.')
    filas = [f for f in filas if any(str(c).strip() for c in f)]
    if not filas:
        raise ErrorSupervision('El archivo no tiene filas.')
    return filas


def filas_desde_archivo(archivo) -> list:
    """Filas {correo, nombre?, programa?, semestre?, codigo?} según el encabezado.

    Sin encabezado reconocible se toma la primera columna como correo.
    """
    filas = _leer_tabla(archivo)
    encabezado = [_normalizar(c) for c in filas[0]]
    columnas = {}
    for i, titulo in enumerate(encabezado):
        for campo, alias in COLUMNAS.items():
            if titulo in alias and campo not in columnas:
                columnas[campo] = i
    if 'correo' in columnas:
        filas = filas[1:]
    else:
        columnas = {'correo': 0}
    salida = []
    for f in filas:
        fila = {}
        for campo, i in columnas.items():
            fila[campo] = str(f[i]).strip() if i < len(f) and f[i] is not None else ''
        salida.append(fila)
    return salida


def correos_desde_archivo(archivo) -> list:
    """Compatibilidad: solo los correos."""
    return [f['correo'] for f in filas_desde_archivo(archivo)]


def _datos_sistema(usuario) -> dict:
    perfil = getattr(usuario, 'perfil_academico', None)
    return {
        'nombre': nombre_completo(usuario),
        'codigo': perfil.codigo_matricula if perfil else None,
        'programa': (f'{perfil.programa.codigo} · {perfil.programa.nombre}' if perfil and perfil.programa_id else None),
        'programa_codigo': perfil.programa.codigo if perfil and perfil.programa_id else None,
        'semestre': perfil.semestre_actual if perfil else None,
        'tiene_perfil': perfil is not None,
    }


def _diferencias(archivo: dict, sistema: dict) -> list:
    """Campos del archivo que no coinciden con la cuenta. Nunca se sobrescriben: solo se informan."""
    difieren = []
    if archivo.get('nombre') and _normalizar(archivo['nombre']) != _normalizar(sistema['nombre']):
        difieren.append('nombre')
    if archivo.get('codigo') and sistema['codigo'] and _normalizar(archivo['codigo']) != _normalizar(sistema['codigo']):
        difieren.append('codigo')
    if archivo.get('programa') and sistema['programa_codigo']:
        valor = _normalizar(archivo['programa'])
        if valor not in (_normalizar(sistema['programa_codigo']), _normalizar(sistema['programa'].split(' · ', 1)[1])):
            difieren.append('programa')
    if archivo.get('semestre') and sistema['semestre'] is not None and str(archivo['semestre']).strip() != str(sistema['semestre']):
        difieren.append('semestre')
    return difieren


def analizar_cargue(evaluacion, filas) -> dict:
    """Clasifica cada fila sin escribir nada.

    `filas`: lista de correos (str) o de dicts {correo, nombre?, programa?, semestre?, codigo?}.
    Con `evaluacion=None` es la validación global del Administrador (sin convocatoria).
    """
    from apps.users.models import User

    if len(filas) > MAX_FILAS_CARGUE:
        raise ErrorSupervision(f'El cargue admite máximo {MAX_FILAS_CARGUE} filas.')
    if not filas:
        raise ErrorSupervision('No hay filas para cargar.')
    filas = [f if isinstance(f, dict) else {'correo': f} for f in filas]
    origenes = origenes_convocatoria(evaluacion) if evaluacion is not None else {}
    normalizados = [str(f.get('correo') or '').strip().lower() for f in filas]
    usuarios = {
        u.email_normalizado: u
        for u in User.objects.annotate(email_normalizado=Lower('email'))
        .filter(email_normalizado__in=set(normalizados))
        .select_related('role', 'perfil_academico__programa')
    }
    vistos = set()
    resultado = []
    for numero, (original, correo) in enumerate(zip(filas, normalizados), start=1):
        archivo = {k: str(original.get(k) or '').strip() for k in ('nombre', 'programa', 'semestre', 'codigo')}
        archivo = {k: v for k, v in archivo.items() if v}
        fila = {'fila': numero, 'correo': correo, 'estado': '', 'estudiante': None, 'nombre': None,
                'origen': None, 'archivo': archivo, 'sistema': None, 'diferencias': []}
        if not correo:
            fila['estado'] = 'campo_obligatorio_faltante'
            resultado.append(fila)
            continue
        try:
            validate_email(correo)
            valido = True
        except ValidationError:
            valido = False
        usuario = usuarios.get(correo)
        if not valido:
            fila['estado'] = 'invalido'
        elif correo in vistos:
            fila['estado'] = 'duplicado_en_archivo'
        elif usuario is None:
            fila['estado'] = 'no_encontrado'
        elif not usuario.role or usuario.role.name != 'Estudiante':
            fila['estado'] = 'no_es_estudiante'
        elif evaluacion is None:
            fila['estado'] = 'existe'
        elif usuario.id in origenes:
            fila['estado'] = 'ya_convocado'
            fila['origen'] = origenes[usuario.id]
        else:
            fila['estado'] = 'agregar'
        if valido:
            vistos.add(correo)
        if usuario is not None and fila['estado'] != 'duplicado_en_archivo':
            fila['estudiante'] = usuario.id
            fila['nombre'] = nombre_completo(usuario)
            fila['sistema'] = _datos_sistema(usuario)
            fila['diferencias'] = _diferencias(archivo, fila['sistema'])
        resultado.append(fila)
    totales = dict.fromkeys(ESTADOS_CARGUE if evaluacion is not None else ESTADOS_VALIDACION, 0)
    for f in resultado:
        totales[f['estado']] = totales.get(f['estado'], 0) + 1
    return {
        'filas': resultado, 'totales': totales, 'total_filas': len(resultado),
        'con_diferencias': sum(1 for f in resultado if f['diferencias']),
        'columnas': sorted({k for f in resultado for k in f['archivo']}),
    }


def confirmar_cargue(evaluacion, informe, por) -> int:
    ids = [f['estudiante'] for f in informe['filas'] if f['estado'] == 'agregar']
    antes = evaluacion.convocados_extra.count()
    ConvocadoEvaluacion.objects.bulk_create(
        [ConvocadoEvaluacion(evaluacion=evaluacion, estudiante_id=i, agregado_por=por) for i in ids],
        ignore_conflicts=True,
    )
    return evaluacion.convocados_extra.count() - antes
