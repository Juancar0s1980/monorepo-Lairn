"""Guía del centro de ayuda para las notas del momento (ADR-019). Crea solo las guías que faltan."""

from django.db import migrations


def sembrar(apps, schema_editor):
    from apps.evaluacion_resultados.services.guias_ayuda import sembrar as sembrar_guias

    sembrar_guias(apps.get_model('evaluacion_resultados', 'ArticuloAyuda'))


class Migration(migrations.Migration):
    dependencies = [('evaluacion_resultados', '0013_esquema_institucional')]
    operations = [migrations.RunPython(sembrar, migrations.RunPython.noop)]
