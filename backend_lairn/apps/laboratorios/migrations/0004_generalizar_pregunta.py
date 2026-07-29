# Migración escrita a mano (no por makemigrations) para preservar los datos
# existentes: usa RenameModel/RenameField en vez de dejar que la detección
# automática de renombres (que no funciona de forma no interactiva) borre y
# recree las tablas.
#
# Generaliza PreguntaCodigo/EntregaCodigo a Pregunta/Entrega (pueden ser de
# tipo "codigo" o "respuesta_libre", para cualquier carrera) y vincula
# Laboratorio con campo_estudio.TemaEstudio (laboratorio de práctica de un
# tema del Campo de Estudio).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratorios', '0003_laboratorio_fecha_limite_laboratorio_max_intentos_and_more'),
        ('campo_estudio', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(old_name='PreguntaCodigo', new_name='Pregunta'),
        migrations.RenameModel(old_name='EntregaCodigo', new_name='Entrega'),
        migrations.RenameField(model_name='entrega', old_name='codigo', new_name='respuesta'),
        migrations.AlterModelTable(name='pregunta', table='preguntas_laboratorio'),
        migrations.AlterModelTable(name='entrega', table='entregas_laboratorio'),
        migrations.AddField(
            model_name='pregunta',
            name='tipo',
            field=models.CharField(
                choices=[('codigo', 'Código'), ('respuesta_libre', 'Respuesta abierta')],
                default='codigo',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='entrega',
            name='estudiante',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='entregas_laboratorio',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='laboratorio',
            name='tema_estudio',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='laboratorios_practica',
                to='campo_estudio.temaestudio',
            ),
        ),
    ]
