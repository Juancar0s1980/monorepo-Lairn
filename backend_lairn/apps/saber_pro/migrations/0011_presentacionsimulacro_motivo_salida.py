from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saber_pro', '0010_simulacro_codigo_desbloqueo_hash_presentacionsimulacro_bloqueada'),
    ]

    operations = [
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
                ],
                default='',
                max_length=20,
            ),
        ),
    ]
