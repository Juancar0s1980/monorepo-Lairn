"""Siembra los videos del centro de ayuda (ADR-018).

Los videos viven versionados en `semillas/videos_ayuda/<slug>.mp4` porque `media/` no se sube al
repositorio. Esta migración los copia al almacenamiento de archivos (MEDIA) y los enlaza a su guía,
igual que la carga manual del Administrador (`<slug>.mp4` en `ayuda/videos/`).

Solo completa guías sin video: nunca reemplaza un video que el Administrador ya haya subido, y
volver a ejecutarla no duplica archivos. La reversión no borra nada.
"""

from pathlib import Path

from django.core.files import File
from django.db import migrations

CARPETA = Path(__file__).resolve().parent.parent / 'semillas' / 'videos_ayuda'


def sembrar_videos(apps, schema_editor):
    # La base de pruebas (test_*) también migra: ahí no se copian 150 MB de videos a MEDIA.
    if str(schema_editor.connection.settings_dict.get('NAME', '')).startswith('test_') or not CARPETA.is_dir():
        return
    ArticuloAyuda = apps.get_model('evaluacion_resultados', 'ArticuloAyuda')
    for ruta in sorted(CARPETA.glob('*.mp4')):
        articulo = ArticuloAyuda.objects.filter(slug=ruta.stem).first()
        if articulo is None or articulo.video:
            continue
        with ruta.open('rb') as archivo:
            articulo.video.save(ruta.name, File(archivo), save=False)
        articulo.video_nombre = ruta.name
        articulo.save(update_fields=['video', 'video_nombre'])


class Migration(migrations.Migration):

    dependencies = [
        ('evaluacion_resultados', '0014_guia_notas_momento'),
    ]

    operations = [
        migrations.RunPython(sembrar_videos, migrations.RunPython.noop),
    ]
