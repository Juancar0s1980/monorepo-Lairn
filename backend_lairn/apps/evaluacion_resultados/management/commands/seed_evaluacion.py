"""
Seed de datos de prueba (lo que pidió TI: poblar con datos falsos).

Uso:
  docker compose exec web python manage.py seed_evaluacion

Idempotente: si ya existe el programa SEMILLA, no duplica nada.
Crea: programa Ing. Software (8 sem), semestres 1-8, 3 asignaturas,
2 competencias, 3 RAs DCE, momentos 4-6-8 con vínculos.
"""

from django.core.management.base import BaseCommand

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    Competencia,
    MomentoEvaluacion,
    MomentoResultado,
    OpcionesOrigen,
    ProgramaAcademico,
    ResultadoAprendizaje,
    SemestrePrograma,
)


class Command(BaseCommand):
    help = 'Siembra estructura académica de prueba (idempotente).'

    def handle(self, *args, **options):
        programa, creado = ProgramaAcademico.objects.get_or_create(
            codigo='ISW-2026',
            defaults={
                'nombre': 'Ingeniería de Software y Computación (prueba)',
                'modalidad': 'Presencial',
                'sede': 'Principal',
                'duracion_semestres': 8,
                'origen': OpcionesOrigen.SEMILLA,
            },
        )
        if not creado:
            self.stdout.write(self.style.WARNING('Programa semilla ya existe, no se duplica.'))
            return

        for numero in range(1, 9):
            SemestrePrograma.objects.create(
                programa=programa, numero=numero, origen=OpcionesOrigen.SEMILLA,
            )

        sem4 = SemestrePrograma.objects.get(programa=programa, numero=4)
        asig1 = AsignaturaMalla.objects.create(
            programa=programa, semestre=sem4, codigo='ISW401',
            nombre='Estructuras de Datos (prueba)', creditos=4,
            intensidad_horaria=6, tipo='obligatoria',
            origen=OpcionesOrigen.SEMILLA,
        )
        comp_esp = Competencia.objects.create(
            programa=programa, nombre='Diseño de software',
            tipo='especifica', descripcion='Diseña soluciones de software.',
            origen=OpcionesOrigen.SEMILLA,
        )
        comp_tra = Competencia.objects.create(
            programa=programa, nombre='Comunicación escrita',
            tipo='transversal', descripcion='Comunica ideas por escrito.',
            origen=OpcionesOrigen.SEMILLA,
        )
        ra1 = ResultadoAprendizaje.objects.create(
            competencia=comp_esp, asignatura=asig1,
            descripcion='Implementar estructuras lineales en un lenguaje de programación.',
            evidencia_observable='Código que pasa casos de prueba definidos.',
            tarea_sugerida='Laboratorio juez en línea con casos públicos/ocultos.',
            criterios_rubrica=[
                {'criterio': 'Correctitud', 'niveles': 'bajo/básico/alto', 'peso': 60},
                {'criterio': 'Eficiencia', 'niveles': 'bajo/básico/alto', 'peso': 40},
            ],
            origen=OpcionesOrigen.SEMILLA,
        )
        for semestre in (4, 6, 8):
            momento = MomentoEvaluacion.objects.create(
                programa=programa, semestre_referencia=semestre,
                nombre=f'Momento {semestre} (prueba)',
                origen=OpcionesOrigen.SEMILLA,
            )
            MomentoResultado.objects.create(
                momento=momento, resultado=ra1, obligatorio=True,
                origen=OpcionesOrigen.SEMILLA,
            )
        self.stdout.write(self.style.SUCCESS('Seed evaluacion_resultados OK (programa ISW-2026).'))
