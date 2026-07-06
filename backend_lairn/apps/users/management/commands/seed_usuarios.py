from django.core.management.base import BaseCommand
from apps.users.models.user import User
from apps.users.models.role import Role


class Command(BaseCommand):
    help = 'Crea un usuario de prueba por cada rol del sistema'

    def handle(self, *args, **kwargs):
        usuarios = [
            {
                'first_name': 'Admin',
                'second_name': '',
                'first_last_name': 'Principal',
                'second_last_name': '',
                'email': 'admin@pseudotutor.com',
                'password': 'Admin1234*',
                'rol': 'Administrador',
                'is_staff': True,
            },
            {
                'first_name': 'Docente',
                'second_name': '',
                'first_last_name': 'Prueba',
                'second_last_name': '',
                'email': 'docente@pseudotutor.com',
                'password': 'Docente1234*',
                'rol': 'Docente',
                'is_staff': False,
            },
            {
                'first_name': 'Estudiante',
                'second_name': '',
                'first_last_name': 'Prueba',
                'second_last_name': '',
                'email': 'estudiante@pseudotutor.com',
                'password': 'Estudiante1234*',
                'rol': 'Estudiante',
                'is_staff': False,
            },
        ]

        for datos in usuarios:
            if User.objects.filter(email=datos['email']).exists():
                self.stdout.write(f'Usuario "{datos["email"]}" ya existe, se omite.')
                continue

            try:
                rol = Role.objects.get(name=datos['rol'])
            except Role.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'Rol "{datos["rol"]}" no encontrado. Ejecuta primero: python manage.py seed_roles'
                ))
                return

            usuario = User.objects.create_user(
                email=datos['email'],
                password=datos['password'],
                first_name=datos['first_name'],
                second_name=datos['second_name'],
                first_last_name=datos['first_last_name'],
                second_last_name=datos['second_last_name'],
                is_staff=datos['is_staff'],
                role=rol,
            )
            self.stdout.write(self.style.SUCCESS(
                f'Usuario "{usuario.email}" creado con rol "{rol.name}".'
            ))
