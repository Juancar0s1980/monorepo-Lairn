from django.core.management.base import BaseCommand
from apps.users.models.role import Role


class Command(BaseCommand):
    help = 'Inserta los roles base del sistema: Administrador, Docente, Estudiante'

    def handle(self, *args, **kwargs):
        roles = ['Administrador', 'Docente', 'Estudiante']
        for nombre in roles:
            rol, creado = Role.objects.get_or_create(name=nombre)
            if creado:
                self.stdout.write(self.style.SUCCESS(f'Rol "{nombre}" creado correctamente.'))
            else:
                self.stdout.write(f'Rol "{nombre}" ya existe, se omite.')
