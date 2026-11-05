from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saber_pro', '0009_presentacionsimulacro_calificacion_docente_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='simulacro',
            name='codigo_desbloqueo_hash',
            field=models.CharField(blank=True, default='', help_text='Hash del codigo que el docente usa para desbloquear un intento.', max_length=128),
        ),
        migrations.AddField(
            model_name='presentacionsimulacro',
            name='bloqueada',
            field=models.BooleanField(default=False, help_text='El intento se bloqueo por una salida detectada y espera el codigo docente.'),
        ),
    ]
