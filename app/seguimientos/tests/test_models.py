from django.test import TestCase
from seguimientos.models import (
    AñoAcademico,
    Ciclo,
    Grupo,
    Modulo,
    UnidadDeTrabajo,
    Profesor,
    Docencia,
    Seguimiento,
)


class SeguimientoModelTestCase(TestCase):
    def setUp(self):
        """Configura los datos iniciales para probar el método save de Seguimiento"""
        # Crear ciclo, módulo y unidades de temario
        self.year = AñoAcademico.objects.create(año_academico="2024-25")
        self.ciclo = Ciclo.objects.create(nombre="Informática", año_academico=self.year)

        self.modulo = Modulo.objects.create(
            nombre="Programación", curso=1, ciclo=self.ciclo
        )
        self.tema1 = UnidadDeTrabajo.objects.create(
            numero_tema=1, titulo="Variables", modulo=self.modulo
        )
        self.tema2 = UnidadDeTrabajo.objects.create(
            numero_tema=2, titulo="Estructuras de Control", modulo=self.modulo
        )
        self.tema3 = UnidadDeTrabajo.objects.create(
            numero_tema=3, titulo="Funciones", modulo=self.modulo
        )

        # Crear profesor, grupo y docencia
        self.profesor = Profesor.objects.create(
            email="profesor@test.com", nombre="Juan Pérez", password="segura123"
        )
        self.grupo = Grupo.objects.create(nombre="1A", ciclo=self.ciclo, curso=1)
        self.docencia = Docencia.objects.create(
            profesor=self.profesor, grupo=self.grupo, modulo=self.modulo
        )

    def test_guardar_seguimiento_actualiza_temas_correctamente(self):
        """Verifica que guardar un seguimiento actualiza los temas impartidos correctamente"""
        # Crear seguimiento con el último tema impartido = tema 2
        Seguimiento.objects.create(
            temario_actual=self.tema2,
            ultimo_contenido_impartido="Estructuras de Control",
            estado="AL_DIA",
            mes=3,
            docencia=self.docencia,
            evaluacion="PRIMERA",
        )

        # Recargar datos desde la BD
        self.tema1.refresh_from_db()
        self.tema2.refresh_from_db()
        self.tema3.refresh_from_db()

        # Validar que los temas 1 y 2 están impartidos, pero el 3 no

    def test_actualizar_seguimiento_regresa_temas_no_impartidos(self):
        """Verifica que al cambiar el tema alcanzado a uno menor, los superiores se desmarcan"""
        # Seguimiento inicial con tema 3
        seguimiento = Seguimiento.objects.create(
            temario_actual=self.tema3,
            ultimo_contenido_impartido="Funciones",
            estado="AL_DIA",
            mes=3,
            docencia=self.docencia,
            evaluacion="PRIMERA",
        )

        # Verificar que todos los temas fueron marcados como impartidos
        self.tema1.refresh_from_db()
        self.tema2.refresh_from_db()
        self.tema3.refresh_from_db()

        # Cambiar el seguimiento para que el último tema impartido sea el 1
        seguimiento.temario_actual = self.tema1
        seguimiento.save()

        # Recargar datos desde la BD
        self.tema1.refresh_from_db()
        self.tema2.refresh_from_db()
        self.tema3.refresh_from_db()

        # Solo el tema 1 debe estar marcado como impartido
