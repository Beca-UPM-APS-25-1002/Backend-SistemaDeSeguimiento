from django.test import TestCase
from rest_framework.test import APIClient

from django.urls import reverse

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


class SeguimientoSerializerTests(TestCase):
    def setUp(self):
        # Crear datos de prueba
        self.client = APIClient()
        self.year = AñoAcademico.objects.create(año_academico="2024-25")
        self.ciclo = Ciclo.objects.create(
            nombre="Desarrollo de Aplicaciones Web", año_academico=self.year
        )
        self.grupo = Grupo.objects.create(nombre="DAW1A", ciclo=self.ciclo, curso=1)
        self.modulo1 = Modulo.objects.create(
            nombre="Programación",
            curso=1,
            ciclo=self.ciclo,
        )
        self.modulo2 = Modulo.objects.create(
            nombre="Bases de Datos",
            curso=1,
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
        self.temario1 = UnidadDeTrabajo.objects.create(
            numero_tema=1, titulo="Introducción a la Programación", modulo=self.modulo1
        )
        self.temario2 = UnidadDeTrabajo.objects.create(
            numero_tema=1,
            titulo="Introducción a las Bases de Datos",
            modulo=self.modulo2,
        )

    def test_validate_temario_pertenece_al_modulo_de_docencia(self):
        url = reverse("seguimiento-list")
        data = {
            "temario_actual": self.temario1.pk,
            "docencia": self.docencia.pk,
            "mes": 10,
            "ultimo_contenido_impartido": "Clases y objetos",
            "estado": "AL_DIA",
            "evaluacion": "PRIMERA",
        }
        self.client.force_authenticate(user=self.profesor)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_validate_temario_no_pertenece_al_modulo_de_docencia(self):
        url = reverse("seguimiento-list")
        data = {
            "temario_actual": self.temario2.pk,
            "docencia": self.docencia.pk,
            "mes": 10,
            "ultimo_contenido_impartido": "Clases y objetos",
            "estado": "AL_DIA",
            "evaluacion": "PRIMERA",
        }
        self.client.force_authenticate(user=self.profesor)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("temario_actual", response.json())

    def test_validate_no_duplicado_mes_grupo_modulo(self):
        Seguimiento.objects.create(
            temario_actual=self.temario1,
            docencia=self.docencia,
            mes=10,
            ultimo_contenido_impartido="Clases y objetos",
            estado="AL_DIA",
            evaluacion="PRIMERA",
        )
        url = reverse("seguimiento-list")
        data = {
            "temario_actual": self.temario1.pk,
            "docencia": self.docencia2.pk,
            "mes": 10,
            "ultimo_contenido_impartido": "Herencia",
            "estado": "ATRASADO",
            "evaluacion": "PRIMERA",
        }
        self.client.force_authenticate(user=self.profesor2)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("docencia", response.json())

    def test_validate_seguimiento_valido(self):
        url = reverse("seguimiento-list")
        data = {
            "temario_actual": self.temario1.pk,
            "docencia": self.docencia.pk,
            "mes": 11,
            "ultimo_contenido_impartido": "Polimorfismo",
            "estado": "ADELANTADO",
            "evaluacion": "PRIMERA",
        }
        self.client.force_authenticate(user=self.profesor)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_validate_post_creacion_correcta(self):
        """
        Verifica que se puede crear un Seguimiento válido con una solicitud POST.
        """
        url = reverse("seguimiento-list")
        data = {
            "temario_actual": self.temario1.pk,
            "docencia": self.docencia.pk,
            "mes": 9,
            "ultimo_contenido_impartido": "Estructuras de control",
            "estado": "AL_DIA",
            "evaluacion": "PRIMERA",
        }
        self.client.force_authenticate(user=self.profesor)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_validate_post_duplicado(self):
        """
        Verifica que no se pueda crear un Seguimiento duplicado en un POST.
        """
        Seguimiento.objects.create(
            temario_actual=self.temario1,
            docencia=self.docencia,
            mes=9,
            ultimo_contenido_impartido="Estructuras de control",
            estado="AL_DIA",
            evaluacion="PRIMERA",
        )
        url = reverse("seguimiento-list")
        data = {
            "temario_actual": self.temario1.pk,
            "docencia": self.docencia.pk,
            "mes": 9,
            "ultimo_contenido_impartido": "Herencia",
            "estado": "ATRASADO",
            "evaluacion": "PRIMERA",
        }
        self.client.force_authenticate(user=self.profesor)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_validate_put_cambio_mes_docencia(self):
        """
        Verifica que no se pueda cambiar el mes o la docencia en un PUT.
        """
        seguimiento = Seguimiento.objects.create(
            temario_actual=self.temario1,
            docencia=self.docencia,
            mes=9,
            ultimo_contenido_impartido="Estructuras de control",
            estado="AL_DIA",
            evaluacion="PRIMERA",
        )
        url = reverse("seguimiento-detail", args=[seguimiento.pk])
        data = {
            "temario_actual": self.temario1.pk,
            "docencia": self.docencia.pk,
            "mes": 10,  # Intento de cambiar el mes
            "ultimo_contenido_impartido": "Herencia",
            "estado": "ATRASADO",
            "evaluacion": "PRIMERA",
        }
        self.client.force_authenticate(user=self.profesor)
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("docencia", response.json())
