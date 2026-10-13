"""
Importador NOVA idempotente (HU-03.1 / 03.2 en modo compatible).

Contrato JSON aceptado (el mismo de tu correo TI):
{
  "programas": [{codigo, nombre, modalidad, sede, duracion, vigencia,
                 external_id?, semestres?: [1,2,...]}],
  "asignaturas": [{codigo, nombre, creditos, intensidad, tipo,
                    programa_codigo, semestre, external_id?}],
  "usuarios": [{email, nombres, apellidos, documento, rol,
                programa_codigo, estado, external_id?}]
}

- `modo='simulacro'`: valida todo sin escribir (dry-run para TI).
- `modo='real'`: `update_or_create` por `codigo`/`external_id`: nunca
  duplica aunque se ejecute N veces.
- Siempre deja `RegistroSincronizacion` + retorna resumen para la UI.
"""

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    OpcionesEstadoRevision,
    OpcionesOrigen,
    ProgramaAcademico,
    SemestrePrograma,
)
from apps.users.models import Role
from .servicio_trazabilidad import registrar_sincronizacion


def _get_or_create_semestres(programa, numeros: list) -> None:
    for numero in numeros or []:
        SemestrePrograma.objects.get_or_create(
            programa=programa,
            numero=int(numero),
            defaults={
                'origen': OpcionesOrigen.API_NOVA,
                'estado_revision': OpcionesEstadoRevision.APROBADO,
            },
        )


@transaction.atomic
def importar_programas_json(payload: dict, *, modo: str = 'simulacro', ejecutado_por=None) -> dict:
    programas = payload.get('programas', [])
    asignaturas = payload.get('asignaturas', [])
    usuarios = payload.get('usuarios', [])
    errores: list = []
    creados = actualizados = omitidos = 0
    mapa_programas: dict = {}

    # 1. Programas (clave natural: codigo).
    for item in programas:
        codigo = (item.get('codigo') or '').strip()
        if not codigo:
            omitidos += 1
            errores.append('Programa sin código omitido.')
            continue
        if modo == 'simulacro':
            creados += 1
            # Centinela: en simulacro el programa aún no existe en BD,
            # pero "existirá" tras el import; las asignaturas del mismo
            # lote deben resolverlo contra este mapa y no contra la BD.
            mapa_programas[codigo] = 'simulacro'
            continue
        programa, es_nuevo = ProgramaAcademico.objects.update_or_create(
            codigo=codigo,
            defaults={
                'nombre': item.get('nombre', codigo)[:200],
                'modalidad': item.get('modalidad', 'Presencial')[:30],
                'sede': item.get('sede', 'Principal')[:100],
                'duracion_semestres': int(item.get('duracion') or 8),
                'origen': OpcionesOrigen.API_NOVA,
                'external_id': item.get('external_id'),
                'datos_origen': item,
                'estado_revision': OpcionesEstadoRevision.APROBADO,
                'activo': True,
            },
        )
        mapa_programas[codigo] = programa
        _get_or_create_semestres(programa, item.get('semestres'))
        creados, actualizados = (creados + 1, actualizados) if es_nuevo else (creados, actualizados + 1)

    # 2. Asignaturas (clave natural: codigo).
    for item in asignaturas:
        codigo = (item.get('codigo') or '').strip()
        prog_codigo = (item.get('programa_codigo') or '').strip()
        if not codigo or not prog_codigo:
            omitidos += 1
            errores.append(f'Asignatura {codigo or "?"} sin código o programa: omitida.')
            continue
        programa = mapa_programas.get(prog_codigo) or ProgramaAcademico.objects.filter(codigo=prog_codigo).first()
        if programa is None:
            omitidos += 1
            errores.append(f'Asignatura {codigo}: programa {prog_codigo} no existe.')
            continue
        if modo == 'simulacro':
            creados += 1
            continue
        semestre = None
        if item.get('semestre'):
            semestre, _ = SemestrePrograma.objects.get_or_create(
                programa=programa, numero=int(item['semestre']),
                defaults={'origen': OpcionesOrigen.API_NOVA},
            )
        _, es_nuevo = AsignaturaMalla.objects.update_or_create(
            codigo=codigo,
            defaults={
                'programa': programa,
                'semestre': semestre,
                'nombre': item.get('nombre', codigo)[:200],
                'creditos': int(item.get('creditos') or 3),
                'intensidad_horaria': int(item.get('intensidad') or 0),
                'tipo': (item.get('tipo') or 'obligatoria')[:20],
                'origen': OpcionesOrigen.API_NOVA,
                'external_id': item.get('external_id'),
                'datos_origen': item,
                'estado_revision': OpcionesEstadoRevision.APROBADO,
                'activo': True,
            },
        )
        creados, actualizados = (creados + 1, actualizados) if es_nuevo else (creados, actualizados + 1)

    # 3. Usuarios: solo valida en simulacro; la creación real la hace el
    # equipo TI en sesión (no auto-creamos cuentas con datos no verificados).
    User = get_user_model()
    for item in usuarios:
        email = (item.get('email') or '').strip().lower()
        if not email:
            omitidos += 1
            errores.append('Usuario sin email omitido.')
            continue
        if modo == 'simulacro':
            if not User.objects.filter(email=email).exists():
                creados += 1
            else:
                actualizados += 1
            continue
        # En modo real solo reportamos coincidencia, no creamos (seguridad).
        if User.objects.filter(email=email).exists():
            actualizados += 1
        else:
            omitidos += 1
            errores.append(f'{email}: no existe en PseudoTutor, pendiente de alta por TI.')

    total = len(programas) + len(asignaturas) + len(usuarios)
    registro = registrar_sincronizacion(
        origen='api_nova_json',
        entidad='programas/asignaturas/usuarios',
        modo=modo,
        total_recibidos=total,
        creados=creados,
        actualizados=actualizados,
        omitidos=omitidos,
        errores=errores[:50],
        ejecutado_por=ejecutado_por,
    )
    return {
        'registro_id': registro.id,
        'modo': modo,
        'total_recibidos': total,
        'creados': creados,
        'actualizados': actualizados,
        'omitidos': omitidos,
        'errores': errores[:50],
    }
