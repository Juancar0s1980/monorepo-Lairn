"""
Comando seed del módulo Saber Pro.

Crea el catálogo de `AreaSaberPro` necesario para que el docente pueda crear
cursos (HU-17.1). Es idempotente (usa `get_or_create`, mismo criterio que
`seed_roles`) para poder ejecutarse repetidamente sin romper datos ni duplicar
las áreas existentes.

Ejecución:
    docker compose exec web python manage.py seed_saber_pro
"""

from django.core.management.base import BaseCommand

from apps.saber_pro.models.area_saber_pro import AreaSaberPro


# Catálogo institucional de áreas de las pruebas Saber Pro, con su descripción
# y el orden con que se presentan en la interfaz (HU-16/17).
AREAS_SABER_PRO = [
    ('Razonamiento Cuantitativo', 'Competencias de interpretación, formulación y argumentación en contextos matemáticos y esquemáticos.'),
    ('Lectura Crítica', 'Comprensión y reflexión sobre textos continuos y discontinuos.'),
    ('Competencias Ciudadanas', 'Conocimientos, argumentación, multiperspectivismo y pensamiento sistémico.'),
    ('Comunicación Escrita', 'Producción de un texto argumentativo de máximo dos páginas.'),
    ('Inglés', 'Comunicación efectiva en inglés clasificada por niveles del MCER.'),
]


class Command(BaseCommand):
    help = 'Crea el catálogo de áreas Saber Pro (idempotente).'

    def handle(self, *args, **options):
        creadas = 0
        for orden, (nombre, descripcion) in enumerate(AREAS_SABER_PRO, start=1):
            _, creada = AreaSaberPro.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion, 'orden': orden},
            )
            creadas += int(creada)
        self.stdout.write(self.style.SUCCESS(f'Áreas Saber Pro listas ({creadas} nuevas).'))