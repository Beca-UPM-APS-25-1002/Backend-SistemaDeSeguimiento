from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from seguimientos.models import Ciclo, Modulo, UnidadDeTemario


class ModuloViewSetTestCase(APITestCase):
    def setUp(self):
        """Configura los datos iniciales para probar la acción 'temario'"""
        self.ciclo = Ciclo.objects.create(nombre="Informática")

        # Módulo con temario
        self.modulo = Modulo.objects.create(
            nombre="Programación", curso=1, año_academico="2024", ciclo=self.ciclo
        )
        self.tema1 = UnidadDeTemario.objects.create(
            numero_tema=1, titulo="Variables", modulo=self.modulo
        )
        self.tema2 = UnidadDeTemario.objects.create(
            numero_tema=2, titulo="Estructuras de Control", modulo=self.modulo
        )

        # Módulo sin temario
        self.modulo_sin_temario = Modulo.objects.create(
            nombre="Bases de Datos", curso=1, año_academico="2024", ciclo=self.ciclo
        )

        # URLs
        self.temario_url = reverse("modulo-temario", args=[self.modulo.id])
        self.temario_url_sin_datos = reverse(
            "modulo-temario", args=[self.modulo_sin_temario.id]
        )
        self.temario_url_no_existente = reverse("modulo-temario", args=[9999])

    def test_obtener_temario_exitosamente(self):
        """Verifica que 'temario' devuelve las unidades de temario correctamente"""
        response = self.client.get(self.temario_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["titulo"], "Variables")
        self.assertEqual(response.data[1]["titulo"], "Estructuras de Control")

    def test_temario_modulo_sin_unidades(self):
        """Verifica que 'temario' devuelve 404 si no hay unidades de temario"""
        response = self.client.get(self.temario_url_sin_datos)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data, "No existen unidades de temario para este modulo"
        )

    def test_temario_modulo_no_existente(self):
        """Verifica que 'temario' devuelve 404 si el módulo no existe"""
        response = self.client.get(self.temario_url_no_existente)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
