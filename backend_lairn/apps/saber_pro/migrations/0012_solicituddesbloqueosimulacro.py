import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def crear_solicitudes_para_bloqueos_existentes(apps, schema_editor):
    """Convierte los bloqueos del flujo anterior en solicitudes atendibles.

    Antes el docente desbloqueaba con un código; ahora solo puede aprobar una
    solicitud. Los intentos que quedaron bloqueados con el flujo anterior deben
    aparecer en la campana del docente para no dejar al estudiante atascado.
    """
    PresentacionSimulacro = apps.get_model('saber_pro', 'PresentacionSimulacro')
    SolicitudDesbloqueoSimulacro = apps.get_model(
        'saber_pro', 'SolicitudDesbloqueoSimulacro'
    )

    bloqueadas = PresentacionSimulacro.objects.filter(
        bloqueada=True,
        estado='en_progreso',
    )
    for presentacion in bloqueadas.iterator():
        existe_pendiente = SolicitudDesbloqueoSimulacro.objects.filter(
            presentacion=presentacion,
            estado='pendiente',
        ).exists()
        if not existe_pendiente:
            SolicitudDesbloqueoSimulacro.objects.create(
                presentacion=presentacion,
                motivo='cambio_pestana',
            )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('saber_pro', '0011_presentacionsimulacro_motivo_salida'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presentacionsimulacro',
            name='bloqueada',
            field=models.BooleanField(
                default=False,
                help_text='El intento se bloqueó por una salida detectada y espera aprobación docente.',
            ),
        ),
        migrations.CreateModel(
            name='SolicitudDesbloqueoSimulacro',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'motivo',
                    models.CharField(
                        choices=[
                            ('cambio_pestana', 'Cambio de pestaña'),
                            ('pantalla_completa', 'Salida de pantalla completa'),
                            ('perdida_foco', 'Pérdida de foco'),
                        ],
                        default='cambio_pestana',
                        help_text='Evento de seguridad que bloqueó el intento.',
                        max_length=30,
                    ),
                ),
                (
                    'estado',
                    models.CharField(
                        choices=[
                            ('pendiente', 'Pendiente'),
                            ('aprobada', 'Aprobada'),
                            ('rechazada', 'Rechazada'),
                            ('cancelada', 'Cancelada'),
                        ],
                        default='pendiente',
                        max_length=20,
                    ),
                ),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
                ('atendida_en', models.DateTimeField(blank=True, null=True)),
                (
                    'atendida_por',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='solicitudes_desbloqueo_atendidas',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'presentacion',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='solicitudes_desbloqueo',
                        to='saber_pro.presentacionsimulacro',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Solicitud de desbloqueo Saber Pro',
                'verbose_name_plural': 'Solicitudes de desbloqueo Saber Pro',
                'db_table': 'solicitudes_desbloqueo_saber_pro',
                'ordering': ['creada_en', 'id'],
                'indexes': [
                    models.Index(
                        fields=['estado', 'creada_en'],
                        name='solicitud_desbloq_estado_idx',
                    ),
                ],
                'constraints': [
                    models.UniqueConstraint(
                        condition=models.Q(('estado', 'pendiente')),
                        fields=('presentacion',),
                        name='solicitud_desbloqueo_pendiente_unica',
                    ),
                ],
            },
        ),
        migrations.RunPython(
            crear_solicitudes_para_bloqueos_existentes,
            migrations.RunPython.noop,
        ),
    ]
