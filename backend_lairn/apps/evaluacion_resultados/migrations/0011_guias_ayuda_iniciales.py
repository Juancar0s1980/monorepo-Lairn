"""Guías iniciales del centro de ayuda (ADR-018). Idempotente: crea solo las que faltan."""

from django.db import migrations


def sembrar(apps, schema_editor):
    from apps.evaluacion_resultados.services.guias_ayuda import sembrar as sembrar_guias

    sembrar_guias(apps.get_model('evaluacion_resultados', 'ArticuloAyuda'))


class Migration(migrations.Migration):
    dependencies = [('evaluacion_resultados', '0010_articulos_ayuda')]
    operations = [migrations.RunPython(sembrar, migrations.RunPython.noop)]
