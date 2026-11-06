"""
Reevalúa las alertas de bajo desempeño de todos los programas (HU-10.2).

Las alertas también se reevalúan al abrir el tablero y al cambiar la regla;
este comando permite programarlo (p. ej. cron diario):
    docker compose exec web python manage.py evaluar_alertas
"""

from django.core.management.base import BaseCommand

from apps.evaluacion_resultados.services.servicio_alertas import evaluar_alertas


class Command(BaseCommand):
    help = 'Reevalúa las alertas de bajo desempeño según la regla vigente.'

    def handle(self, *args, **kwargs):
        resumen = evaluar_alertas()
        self.stdout.write(self.style.SUCCESS(
            f"Alertas creadas: {resumen['creadas']} · actualizadas: {resumen['actualizadas']} · resueltas: {resumen['resueltas']}"
        ))
