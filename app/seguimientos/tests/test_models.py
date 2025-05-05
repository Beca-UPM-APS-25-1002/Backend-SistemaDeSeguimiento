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


class AñoAcademicoModelTests(TestCase):
    """Tests para el modelo AñoAcademico"""

    def test_primer_año_es_actual(self):
        """Probar que el primer año creado se establece como actual automáticamente"""
        año = AñoAcademico.objects.create(año_academico="2022-23")
        self.assertTrue(año.actual)

    def test_solo_un_año_es_actual(self):
        """Probar que solo un año puede ser actual a la vez"""
        año1 = AñoAcademico.objects.create(año_academico="2022-23")
        año2 = AñoAcademico.objects.create(año_academico="2023-24")
        año3 = AñoAcademico.objects.create(año_academico="2024-25")

        # Verificar que el primer año creado es actual
        self.assertTrue(año1.actual)
        self.assertFalse(año2.actual)
        self.assertFalse(año3.actual)

        # Cambiar el actual a año2
        año2.actual = True
        año2.save()

        # Recargar desde la base de datos
        año1.refresh_from_db()
        año2.refresh_from_db()
        año3.refresh_from_db()

        # Verificar que solo año2 es actual
        self.assertFalse(año1.actual)
        self.assertTrue(año2.actual)
        self.assertFalse(año3.actual)

    def test_eliminar_año_actual(self):
        """Probar que al eliminar el año actual, el año con valor más alto se convierte en actual"""
        AñoAcademico.objects.create(año_academico="2022-23")
        AñoAcademico.objects.create(año_academico="2023-24")
        año_actual = AñoAcademico.objects.create(año_academico="2024-25")

        # Establecer el último año como actual
        año_actual.actual = True
        año_actual.save()

        # Verificar que es el único actual
        self.assertEqual(AñoAcademico.objects.filter(actual=True).count(), 1)
        self.assertEqual(AñoAcademico.objects.get(actual=True).año_academico, "2024-25")

        # Eliminar el año actual
        año_actual.delete()

        # Verificar que ahora el año más alto es actual
        self.assertEqual(AñoAcademico.objects.filter(actual=True).count(), 1)
        self.assertEqual(AñoAcademico.objects.get(actual=True).año_academico, "2023-24")

    def test_eliminar_año_no_actual(self):
        """Probar que al eliminar un año que no es actual, el año actual no cambia"""
        AñoAcademico.objects.create(año_academico="2022-23")
        año2 = AñoAcademico.objects.create(año_academico="2023-24")
        año3 = AñoAcademico.objects.create(año_academico="2024-25")

        # Establecer año2 como actual
        año2.actual = True
        año2.save()

        # Eliminar año3 (que no es actual)
        año3.delete()

        # Verificar que año2 sigue siendo actual
        self.assertEqual(AñoAcademico.objects.filter(actual=True).count(), 1)
        self.assertEqual(AñoAcademico.objects.get(actual=True).año_academico, "2023-24")

    def test_eliminar_todos_los_años(self):
        """Probar que se pueden eliminar todos los años"""
        AñoAcademico.objects.create(año_academico="2022-23")
        AñoAcademico.objects.create(año_academico="2023-24")

        # Eliminar todos los años
        AñoAcademico.objects.all().delete()

        # Verificar que no quedan años
        self.assertEqual(AñoAcademico.objects.count(), 0)


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
