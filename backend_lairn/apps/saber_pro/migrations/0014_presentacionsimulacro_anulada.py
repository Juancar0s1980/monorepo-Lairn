from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saber_pro', '0013_alter_presentacionsimulacro_motivo_finalizacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='presentacionsimulacro',
            name='anulada',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'El docente rechazó y anuló el intento: su nota es 0 y el '
                    'estudiante no puede iniciar nuevos intentos de este simulacro.'
                ),
            ),
        ),
        migrations.AlterField(
            model_name='presentacionsimulacro',
            name='motivo_finalizacion',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'Sin finalizar'),
                    ('completada', 'Completada'),
                    ('manual', 'Finalizada manualmente'),
                    ('tiempo_agotado', 'Tiempo agotado'),
                    ('fecha_limite', 'Fecha límite vencida'),
                    ('salida', 'Cerrado por salir de la prueba'),
                    ('rechazado', 'Cerrado por desbloqueo rechazado'),
                    ('anulado', 'Anulado por desbloqueo rechazado'),
                ],
                default='',
                max_length=20,
            ),
        ),
    ]
