from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from seguimientos.models import (
    Ciclo,
    Grupo,
    Modulo,
    Profesor,
    Docencia,
    Seguimiento,
    UnidadDeTemario,
)


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


class SeguimientosFaltantesViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.año_academico = "2024-2025"
        self.mes = 3

        # Crear datos de test
        self.ciclo = Ciclo.objects.create(nombre="Informática")
        self.grupo = Grupo.objects.create(nombre="Grupo A", ciclo=self.ciclo, curso=1)
        self.modulo = Modulo.objects.create(
            nombre="Programación",
            curso=1,
            año_academico=self.año_academico,
            ciclo=self.ciclo,
        )
        self.profesor1 = Profesor.objects.create_user(
            email="profesor1@example.com", nombre="Profesor 1", password="testpass"
        )
        self.profesor2 = Profesor.objects.create_user(
            email="profesor2@example.com", nombre="Profesor 2", password="testpass"
        )
        self.docencia1 = Docencia.objects.create(
            profesor=self.profesor1, grupo=self.grupo, modulo=self.modulo
        )
        self.docencia2 = Docencia.objects.create(
            profesor=self.profesor2, grupo=self.grupo, modulo=self.modulo
        )

        self.unidad = UnidadDeTemario.objects.create(
            numero_tema=1, titulo="Introducción", modulo=self.modulo
        )

    def test_seguimientos_faltantes_inicial(self):
        # Verificar que inicialmente no existen seguimientos
        response = self.client.get(
            reverse(
                "seguimientos-faltantes",
                kwargs={"año_academico": self.año_academico, "mes": self.mes},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data), 2
        )  # Ambas docencias deben estar sin seguimiento

    def test_seguimientos_faltantes_despues_de_un_seguimiento(self):
        # Crear un seguimiento para un profesor
        Seguimiento.objects.create(
            temario_alcanzado=self.unidad,
            ultimo_contenido_impartido="Introducción",
            estado="AL_DIA",
            mes=self.mes,
            docencia=self.docencia1,
        )

        response = self.client.get(
            reverse(
                "seguimientos-faltantes",
                kwargs={"año_academico": self.año_academico, "mes": self.mes},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_seguimientos_faltantes_despues_de_seguimientos_mismo_grupo(self):
        # Crear seguimientos para ambas docencias en el mismo grupo y módulo
        Seguimiento.objects.create(
            temario_alcanzado=self.unidad,
            ultimo_contenido_impartido="Introducción",
            estado="AL_DIA",
            mes=self.mes,
            docencia=self.docencia1,
        )
        Seguimiento.objects.create(
            temario_alcanzado=self.unidad,
            ultimo_contenido_impartido="Introducción",
            estado="AL_DIA",
            mes=self.mes,
            docencia=self.docencia2,
        )

        # Verificar que ninguna docencia está pendiente de seguimiento
        response = self.client.get(
            reverse(
                "seguimientos-faltantes",
                kwargs={"año_academico": self.año_academico, "mes": self.mes},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No debe haber docencias pendientes

    def test_seguimientos_faltantes_diferente_modulo(self):
        # Crear otro módulo y una nueva docencia para ese módulo
        modulo2 = Modulo.objects.create(
            nombre="Bases de Datos",
            curso=1,
            año_academico=self.año_academico,
            ciclo=self.ciclo,
        )
        docencia3 = Docencia.objects.create(
            profesor=self.profesor1, grupo=self.grupo, modulo=modulo2
        )

        # Verificar que la nueva docencia también está sin seguimiento
        response = self.client.get(
            reverse(
                "seguimientos-faltantes",
                kwargs={"año_academico": self.año_academico, "mes": self.mes},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data), 3
        )  # Ahora hay tres docencias sin seguimiento

        # Crear un seguimiento para la nueva docencia
        Seguimiento.objects.create(
            temario_alcanzado=self.unidad,
            ultimo_contenido_impartido="Introducción",
            estado="AL_DIA",
            mes=self.mes,
            docencia=docencia3,
        )

        # Verificar que solo las docencias originales siguen sin seguimiento
        response = self.client.get(
            reverse(
                "seguimientos-faltantes",
                kwargs={"año_academico": self.año_academico, "mes": self.mes},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data), 2
        )  # Solo las dos docencias originales deben estar sin seguimiento
