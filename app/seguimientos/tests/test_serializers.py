from django.test import TestCase
from rest_framework.exceptions import ValidationError
from seguimientos.models import (
    Ciclo,
    Grupo,
    Modulo,
    UnidadDeTemario,
    Profesor,
    Docencia,
    Seguimiento,
)
from seguimientos.serializers import SeguimientoSerializer


class SeguimientoSerializerTests(TestCase):
    def setUp(self):
        # Crear datos de prueba
        self.ciclo = Ciclo.objects.create(nombre="Desarrollo de Aplicaciones Web")
        self.grupo = Grupo.objects.create(nombre="DAW1A", ciclo=self.ciclo, curso=1)
        self.modulo1 = Modulo.objects.create(
            nombre="Programación",
            curso=1,
            año_academico="2023/2024",
            ciclo=self.ciclo,
        )
        self.modulo2 = Modulo.objects.create(
            nombre="Bases de Datos",
            curso=1,
            año_academico="2023/2024",
            ciclo=self.ciclo,
        )
        self.profesor = Profesor.objects.create(
            email="profesor@example.com", nombre="Juan Pérez"
        )
        self.profesor2 = Profesor.objects.create(
            email="profesor2@example.com", nombre="Juan2 Pérez"
        )
        self.docencia = Docencia.objects.create(
            profesor=self.profesor, grupo=self.grupo, modulo=self.modulo1
        )
        self.docencia2 = Docencia.objects.create(
            profesor=self.profesor2, grupo=self.grupo, modulo=self.modulo1
        )
        self.temario1 = UnidadDeTemario.objects.create(
            numero_tema=1, titulo="Introducción a la Programación", modulo=self.modulo1
        )
        self.temario2 = UnidadDeTemario.objects.create(
            numero_tema=1,
            titulo="Introducción a las Bases de Datos",
            modulo=self.modulo2,
        )

    def test_validate_temario_pertenece_al_modulo_de_docencia(self):
        """
        Verifica que el temario_alcanzado pertenezca al mismo módulo que la docencia.
        """
        data = {
            "temario_alcanzado": self.temario1.pk,
            "docencia": self.docencia.pk,
            "mes": 10,
            "ultimo_contenido_impartido": "Clases y objetos",
            "estado": "AL_DIA",
        }
        serializer = SeguimientoSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_validate_temario_no_pertenece_al_modulo_de_docencia(self):
        """
        Verifica que se lance una excepción si el temario_alcanzado no pertenece al módulo de la docencia.
        """
        data = {
            "temario_alcanzado": self.temario2.pk,  # Temario de otro módulo
            "docencia": self.docencia.pk,
            "mes": 10,
            "ultimo_contenido_impartido": "Clases y objetos",
            "estado": "AL_DIA",
        }
        serializer = SeguimientoSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("temario_alcanzado", context.exception.detail)
        self.assertEqual(
            context.exception.detail["temario_alcanzado"][0],
            "El temario alcanzado debe pertenecer al módulo de la docencia.",
        )

    def test_validate_no_duplicado_mes_grupo_modulo(self):
        """
        Verifica que no se pueda crear un Seguimiento duplicado para la misma combinación de mes, grupo y módulo.
        """
        # Crear un Seguimiento existente
        Seguimiento.objects.create(
            temario_alcanzado=self.temario1,
            docencia=self.docencia,
            mes=10,
            ultimo_contenido_impartido="Clases y objetos",
            estado="AL_DIA",
        )

        # Intentar crear un Seguimiento duplicado
        data = {
            "temario_alcanzado": self.temario1.pk,
            "docencia": self.docencia2.pk,
            "mes": 10,  # Mismo mes, grupo y módulo
            "ultimo_contenido_impartido": "Herencia",
            "estado": "ATRASADO",
        }
        serializer = SeguimientoSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("docencia", context.exception.detail)
        self.assertEqual(
            context.exception.detail["docencia"][0],
            "Ya existe un seguimiento para este mes, grupo y módulo.",
        )

    def test_validate_seguimiento_valido(self):
        """
        Verifica que un Seguimiento con datos válidos sea aceptado.
        """
        data = {
            "temario_alcanzado": self.temario1.pk,
            "docencia": self.docencia.pk,
            "mes": 11,  # Mes diferente
            "ultimo_contenido_impartido": "Polimorfismo",
            "estado": "ADELANTADO",
        }
        serializer = SeguimientoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
