"""Esquema institucional inicial (ADR-019): 30 % del momento en el tercer corte y 40 % del corte en la definitiva.

Los pesos examen/trabajo quedan sin definir a propósito: los fija la institución o el gestor del momento.
"""

from decimal import Decimal

from django.db import migrations


def crear(apps, schema_editor):
    Esquema = apps.get_model('evaluacion_resultados', 'EsquemaCalificacion')
    if not Esquema.objects.filter(momento__isnull=True).exists():
        Esquema.objects.create(momento=None, peso_momento_en_corte=Decimal('30'), peso_corte_en_definitiva=Decimal('40'))


class Migration(migrations.Migration):
    dependencies = [('evaluacion_resultados', '0012_esquema_calificacion')]
    operations = [migrations.RunPython(crear, migrations.RunPython.noop)]
