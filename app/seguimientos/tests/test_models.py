from django.test import TestCase
from django.core.exceptions import ValidationError
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

    # Tests para la validación condicional de campos
    def test_justificacion_estado_requerido_cuando_no_al_dia(self):
        """Verifica que justificacion_estado es requerido cuando estado no es AL_DIA"""
        # Intentar crear un seguimiento con estado diferente de AL_DIA sin justificación
        seguimiento = Seguimiento(
            temario_actual=self.tema1,
            ultimo_contenido_impartido="Variables",
            estado="ATRASADO",  # Estado diferente de AL_DIA
            justificacion_estado="",  # Justificación vacía
            mes=3,
            docencia=self.docencia,
            evaluacion="PRIMERA",
            cumple_programacion=True,
        )

        # Debe lanzar ValidationError al llamar a full_clean()
        with self.assertRaises(ValidationError) as context:
            seguimiento.full_clean()

        # Verificar que el error es específicamente sobre justificacion_estado
        self.assertIn("justificacion_estado", context.exception.error_dict)

    def test_justificacion_estado_no_requerido_cuando_al_dia(self):
        """Verifica que justificacion_estado no es requerido cuando estado es AL_DIA"""
        # Crear un seguimiento con estado AL_DIA sin justificación
        seguimiento = Seguimiento(
            temario_actual=self.tema1,
            ultimo_contenido_impartido="Variables",
            estado="AL_DIA",
            justificacion_estado="",  # Justificación vacía
            mes=3,
            docencia=self.docencia,
            evaluacion="PRIMERA",
            cumple_programacion=True,
        )

        # No debe lanzar error al llamar a full_clean()
        try:
            seguimiento.full_clean()
        except ValidationError as e:
            # Si hay error, verificar que no está relacionado con justificacion_estado
            self.assertNotIn("justificacion_estado", e.error_dict)

    def test_justificacion_cumple_programacion_requerido_cuando_false(self):
        """Verifica que justificacion_cumple_programacion es requerido cuando cumple_programacion es False"""
        # Intentar crear un seguimiento con cumple_programacion=False sin justificación
        seguimiento = Seguimiento(
            temario_actual=self.tema1,
            ultimo_contenido_impartido="Variables",
            estado="AL_DIA",
            mes=3,
            docencia=self.docencia,
            evaluacion="PRIMERA",
            cumple_programacion=False,  # No cumple programación
            justificacion_cumple_programacion="",  # Justificación vacía
            motivo_no_cumple_programacion="",  # Motivo vacío
        )

        # Debe lanzar ValidationError al llamar a full_clean()
        with self.assertRaises(ValidationError) as context:
            seguimiento.full_clean()

        # Verificar que los errores son específicamente sobre los campos requeridos
        self.assertIn("justificacion_cumple_programacion", context.exception.error_dict)

    def test_motivo_no_cumple_programacion_requerido_cuando_false(self):
        """Verifica que motivo_no_cumple_programacion es requerido cuando cumple_programacion es False"""
        # Intentar crear un seguimiento con cumple_programacion=False con justificación pero sin motivo
        seguimiento = Seguimiento(
            temario_actual=self.tema1,
            ultimo_contenido_impartido="Variables",
            estado="AL_DIA",
            mes=3,
            docencia=self.docencia,
            evaluacion="PRIMERA",
            cumple_programacion=False,  # No cumple programación
            justificacion_cumple_programacion="Hubo una huelga",  # Justificación proporcionada
            motivo_no_cumple_programacion="",  # Motivo vacío
        )

        # Debe lanzar ValidationError al llamar a full_clean()
        with self.assertRaises(ValidationError) as context:
            seguimiento.full_clean()

        # Verificar que el error es específicamente sobre motivo_no_cumple_programacion
        self.assertIn("motivo_no_cumple_programacion", context.exception.error_dict)

    def test_justificacion_y_motivo_no_requeridos_cuando_cumple_programacion_true(self):
        """Verifica que justificacion_cumple_programacion y motivo_no_cumple_programacion no son requeridos cuando cumple_programacion es True"""
        # Crear un seguimiento con cumple_programacion=True sin justificación ni motivo
        seguimiento = Seguimiento(
            temario_actual=self.tema1,
            ultimo_contenido_impartido="Variables",
            estado="AL_DIA",
            mes=3,
            docencia=self.docencia,
            evaluacion="PRIMERA",
            cumple_programacion=True,  # Cumple programación
            justificacion_cumple_programacion="",  # Justificación vacía
            motivo_no_cumple_programacion="",  # Motivo vacío
        )

        # No debe lanzar error al llamar a full_clean()
        try:
            seguimiento.full_clean()
        except ValidationError as e:
            # Si hay error, verificar que no está relacionado con los campos de justificación
            self.assertNotIn("justificacion_cumple_programacion", e.error_dict)
            self.assertNotIn("motivo_no_cumple_programacion", e.error_dict)
