from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from seguimientos.models import (
    AñoAcademico,
    Ciclo,
    Grupo,
    Modulo,
    Profesor,
    Docencia,
    Seguimiento,
    UnidadDeTrabajo,
)
from django.core import mail
from django.conf import settings
import calendar


class ModuloViewSetTestCase(APITestCase):
    def setUp(self):
        """Configura los datos iniciales para probar la acción 'temario'"""
        self.client = APIClient()
        self.year = AñoAcademico.objects.create(año_academico="2024-25")
        self.ciclo = Ciclo.objects.create(nombre="Informática", año_academico=self.year)

        # Módulo con temario
        self.modulo = Modulo.objects.create(
            nombre="Programación", curso=1, ciclo=self.ciclo
        )
        self.tema1 = UnidadDeTrabajo.objects.create(
            numero_tema=1, titulo="Variables", modulo=self.modulo
        )
        self.tema2 = UnidadDeTrabajo.objects.create(
            numero_tema=2, titulo="Estructuras de Control", modulo=self.modulo
        )

        # Módulo sin temario
        self.modulo_sin_temario = Modulo.objects.create(
            nombre="Bases de Datos", curso=1, ciclo=self.ciclo
        )

        # URLs
        self.temario_url = reverse("modulo-temario", args=[self.modulo.id])
        self.temario_url_sin_datos = reverse(
            "modulo-temario", args=[self.modulo_sin_temario.id]
        )
        self.temario_url_no_existente = reverse("modulo-temario", args=[9999])
        self.profesor1 = Profesor.objects.create_user(
            email="profesor1@example.com",
            nombre="Profesor 1",
            password="testpass",
        )
        self.client.force_authenticate(user=self.profesor1)

    def test_get_temario_exitosamente(self):
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
        self.mes = 3

        # Crear datos de test
        self.year = AñoAcademico.objects.create(año_academico="2024-25")
        self.ciclo = Ciclo.objects.create(nombre="Informática", año_academico=self.year)
        self.grupo = Grupo.objects.create(nombre="Grupo A", ciclo=self.ciclo, curso=1)
        self.modulo = Modulo.objects.create(
            nombre="Programación",
            curso=1,
            ciclo=self.ciclo,
        )
        self.profesor1 = Profesor.objects.create_user(
            email="profesor1@example.com",
            nombre="Profesor 1",
            password="testpass",
        )
        self.profesor2 = Profesor.objects.create_user(
            email="profesor2@example.com", nombre="Profesor 2", password="testpass"
        )
        self.admin = Profesor.objects.create_user(
            email="admin@example.com",
            nombre="admin",
            password="testpass",
            is_admin=True,
        )
        self.docencia1 = Docencia.objects.create(
            profesor=self.profesor1, grupo=self.grupo, modulo=self.modulo
        )
        self.docencia2 = Docencia.objects.create(
            profesor=self.profesor2, grupo=self.grupo, modulo=self.modulo
        )

        self.unidad = UnidadDeTrabajo.objects.create(
            numero_tema=1, titulo="Introducción", modulo=self.modulo
        )

    def test_seguimientos_faltantes_inicial(self):
        # Verificar que inicialmente no existen seguimientos
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            reverse(
                "seguimientos-faltantes",
                kwargs={"año_academico": self.year.año_academico, "mes": self.mes},
            )
            + "?all"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data), 2
        )  # Ambas docencias deben estar sin seguimiento

    def test_seguimientos_faltantes_despues_de_un_seguimiento(self):
        # Crear un seguimiento para un profesor
        Seguimiento.objects.create(
            temario_actual=self.unidad,
            ultimo_contenido_impartido="Introducción",
            estado="AL_DIA",
            mes=self.mes,
            docencia=self.docencia1,
            evaluacion="PRIMERA",
        )
        self.client.force_authenticate(user=self.profesor1)

        response = self.client.get(
            reverse(
                "seguimientos-faltantes",
                kwargs={"año_academico": self.year.año_academico, "mes": self.mes},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_seguimientos_faltantes_despues_de_seguimientos_mismo_grupo(self):
        # Crear seguimientos para ambas docencias en el mismo grupo y módulo
        Seguimiento.objects.create(
            temario_actual=self.unidad,
            ultimo_contenido_impartido="Introducción",
            estado="AL_DIA",
            mes=self.mes,
            docencia=self.docencia1,
            evaluacion="PRIMERA",
        )
        Seguimiento.objects.create(
            temario_actual=self.unidad,
            ultimo_contenido_impartido="Introducción",
            estado="AL_DIA",
            mes=self.mes,
            docencia=self.docencia2,
            evaluacion="PRIMERA",
        )
        self.client.force_authenticate(user=self.profesor1)
        # Verificar que ninguna docencia está pendiente de seguimiento
        response = self.client.get(
            reverse(
                "seguimientos-faltantes",
                kwargs={"año_academico": self.year.año_academico, "mes": self.mes},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No debe haber docencias pendientes

    def test_seguimientos_faltantes_diferente_modulo(self):
        # Crear otro módulo y una nueva docencia para ese módulo
        modulo2 = Modulo.objects.create(
            nombre="Bases de Datos",
            curso=1,
            ciclo=self.ciclo,
        )
        docencia3 = Docencia.objects.create(
            profesor=self.profesor1, grupo=self.grupo, modulo=modulo2
        )
        self.client.force_authenticate(user=self.admin)
        # Verificar que la nueva docencia también está sin seguimiento
        response = self.client.get(
            reverse(
                "seguimientos-faltantes",
                kwargs={"año_academico": self.year.año_academico, "mes": self.mes},
            )
            + "?all"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data), 3
        )  # Ahora hay tres docencias sin seguimiento

        # Crear un seguimiento para la nueva docencia
        Seguimiento.objects.create(
            temario_actual=self.unidad,
            ultimo_contenido_impartido="Introducción",
            estado="AL_DIA",
            mes=self.mes,
            docencia=docencia3,
            evaluacion="PRIMERA",
        )

        # Verificar que solo las docencias originales siguen sin seguimiento
        response = self.client.get(
            reverse(
                "seguimientos-faltantes",
                kwargs={"año_academico": self.year.año_academico, "mes": self.mes},
            )
            + "?all"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data), 2
        )  # Solo las dos docencias originales deben estar sin seguimiento


class SeguimientoViewSetTests(APITestCase):
    """
    Suite de pruebas para el SeguimientoViewSet.
    Verifica que los profesores solo pueden acceder a seguimientos
    donde tienen una docencia con el mismo grupo y módulo.
    """

    def setUp(self):
        """Configuración inicial de datos para las pruebas"""
        self.year = AñoAcademico.objects.create(año_academico="2024-25")

        # Crear ciclos
        self.ciclo1 = Ciclo.objects.create(nombre="DAW", año_academico=self.year)
        self.ciclo2 = Ciclo.objects.create(nombre="DAM", año_academico=self.year)

        # Crear grupos
        self.grupo1 = Grupo.objects.create(nombre="Grupo A", ciclo=self.ciclo1, curso=1)
        self.grupo2 = Grupo.objects.create(nombre="Grupo B", ciclo=self.ciclo2, curso=1)

        # Crear módulos
        self.modulo1 = Modulo.objects.create(
            nombre="Programación", curso=1, ciclo=self.ciclo1
        )
        self.modulo2 = Modulo.objects.create(
            nombre="Bases de Datos",
            curso=1,
            ciclo=self.ciclo1,
        )

        # Crear unidades de temario
        self.unidad1 = UnidadDeTrabajo.objects.create(
            numero_tema=1, titulo="Introducción", modulo=self.modulo1
        )
        self.unidad2 = UnidadDeTrabajo.objects.create(
            numero_tema=1, titulo="Introducción", modulo=self.modulo2
        )

        # Crear profesores
        self.profesor1 = Profesor.objects.create_user(
            email="profesor1@test.com", nombre="Profesor Uno", password="password123"
        )
        self.profesor2 = Profesor.objects.create_user(
            email="profesor2@test.com", nombre="Profesor Dos", password="password123"
        )

        # Crear docencias
        # Profesor 1 tiene docencia en Grupo A, Módulo Programación
        self.docencia1 = Docencia.objects.create(
            profesor=self.profesor1, grupo=self.grupo1, modulo=self.modulo1
        )

        # Profesor 2 tiene docencia en Grupo A, Módulo Bases de Datos
        self.docencia2 = Docencia.objects.create(
            profesor=self.profesor2, grupo=self.grupo1, modulo=self.modulo2
        )

        # Profesor 2 también tiene docencia en Grupo B, Módulo Programación
        self.docencia3 = Docencia.objects.create(
            profesor=self.profesor2, grupo=self.grupo2, modulo=self.modulo1
        )

        # Crear seguimientos
        self.seguimiento1 = Seguimiento.objects.create(
            temario_actual=self.unidad1,
            ultimo_contenido_impartido="Variables y tipos de datos",
            estado="AL_DIA",
            mes=1,
            docencia=self.docencia1,
            evaluacion="PRIMERA",
        )

        self.seguimiento2 = Seguimiento.objects.create(
            temario_actual=self.unidad2,
            ultimo_contenido_impartido="Modelo relacional",
            estado="AL_DIA",
            mes=1,
            docencia=self.docencia2,
            evaluacion="PRIMERA",
        )

        self.seguimiento3 = Seguimiento.objects.create(
            temario_actual=self.unidad1,
            ultimo_contenido_impartido="Estructuras de control",
            estado="ADELANTADO",
            mes=2,
            docencia=self.docencia3,
            evaluacion="PRIMERA",
        )

        # Preparar el cliente API
        self.client = APIClient()

        # URL para la API de seguimientos
        self.url_list = reverse("seguimiento-list")

    def test_unauthenticated_access(self):
        """Prueba que los usuarios no autenticados no pueden acceder a los seguimientos"""
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profesor1_access(self):
        """
        Prueba que el profesor1 solo puede ver los seguimientos relacionados con
        sus docencias (grupo A, módulo programación)
        """
        self.client.force_authenticate(user=self.profesor1)
        response = self.client.get(self.url_list)

        # Verificar código de estado
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que solo obtiene 1 seguimiento (el suyo)
        self.assertEqual(len(response.data), 1)

        # Verificar que es el seguimiento correcto
        self.assertEqual(response.data[0]["id"], self.seguimiento1.id)

    def test_profesor2_access(self):
        """
        Prueba que el profesor2 solo puede ver los seguimientos relacionados con
        sus docencias (grupo A, módulo bases de datos y grupo B, módulo programación)
        """
        self.client.force_authenticate(user=self.profesor2)
        response = self.client.get(self.url_list)

        # Verificar código de estado
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que obtiene 2 seguimientos
        self.assertEqual(len(response.data), 2)

        # Verificar que son los seguimientos correctos
        seguimiento_ids = [item["id"] for item in response.data]
        self.assertIn(self.seguimiento2.id, seguimiento_ids)
        self.assertIn(self.seguimiento3.id, seguimiento_ids)
        self.assertNotIn(self.seguimiento1.id, seguimiento_ids)

    def test_profesor1_create_for_own_docencia(self):
        """
        Prueba que el profesor1 puede crear un seguimiento para su propia docencia
        """
        self.client.force_authenticate(user=self.profesor1)
        data = {
            "temario_actual": self.unidad1.id,
            "ultimo_contenido_impartido": "Funciones y métodos",
            "estado": "AL_DIA",
            "mes": 3,
            "docencia": self.docencia1.id,
            "evaluacion": "PRIMERA",
        }

        response = self.client.post(self.url_list, data, format="json")

        # Verificar que se crea correctamente
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_profesor1_cannot_create_for_other_docencia(self):
        """
        Prueba que el profesor1 no puede crear un seguimiento para la docencia de otro profesor
        """
        self.client.force_authenticate(user=self.profesor1)
        data = {
            "temario_actual": self.unidad2.id,
            "ultimo_contenido_impartido": "Consultas SQL",
            "estado": "AL_DIA",
            "mes": 3,
            "docencia": self.docencia2.id,  # Docencia del profesor2
        }

        response = self.client.post(self.url_list, data, format="json")

        # Verificar que no se permite la creación
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_profesor1_can_update_own_seguimiento(self):
        """
        Prueba que el profesor1 puede actualizar un seguimiento relacionado con su docencia
        """
        self.client.force_authenticate(user=self.profesor1)
        url_detail = reverse("seguimiento-detail", args=[self.seguimiento1.id])
        data = {
            "temario_actual": self.unidad1.id,
            "ultimo_contenido_impartido": "Contenido actualizado",
            "estado": "ADELANTADO",
            "mes": 1,
            "docencia": self.docencia1.id,
            "evaluacion": "PRIMERA",
        }

        response = self.client.put(url_detail, data, format="json")

        # Verificar que se actualiza correctamente
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["ultimo_contenido_impartido"], "Contenido actualizado"
        )

    def test_profesor1_cannot_update_other_seguimiento(self):
        """
        Prueba que el profesor1 no puede actualizar un seguimiento relacionado con la docencia de otro profesor
        """
        self.client.force_authenticate(user=self.profesor1)
        url_detail = reverse("seguimiento-detail", args=[self.seguimiento2.id])
        data = {
            "temario_actual": self.unidad2.id,
            "ultimo_contenido_impartido": "Intento de modificación",
            "estado": "ATRASADO",
            "mes": 1,
            "docencia": self.docencia2.id,
            "evaluacion": "PRIMERA",
        }

        response = self.client.put(url_detail, data, format="json")

        # Verificar que no se permite la actualización
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_profesor1_can_delete_own_seguimiento(self):
        """
        Prueba que el profesor1 puede eliminar un seguimiento relacionado con su docencia
        """
        self.client.force_authenticate(user=self.profesor1)
        url_detail = reverse("seguimiento-detail", args=[self.seguimiento1.id])

        response = self.client.delete(url_detail)

        # Verificar que se elimina correctamente
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verificar que ya no existe el seguimiento
        self.assertFalse(Seguimiento.objects.filter(id=self.seguimiento1.id).exists())

    def test_profesor1_cannot_delete_other_seguimiento(self):
        """
        Prueba que el profesor1 no puede eliminar un seguimiento relacionado con la docencia de otro profesor
        """
        self.client.force_authenticate(user=self.profesor1)
        url_detail = reverse("seguimiento-detail", args=[self.seguimiento2.id])

        response = self.client.delete(url_detail)

        # Verificar que no se permite la eliminación
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verificar que el seguimiento sigue existiendo
        self.assertTrue(Seguimiento.objects.filter(id=self.seguimiento2.id).exists())

    def test_profesor_with_same_grupo_modulo_can_access(self):
        """
        Prueba que un profesor con docencia del mismo grupo y módulo puede acceder
        a seguimientos aunque no sea el profesor asignado a esa docencia específica
        """
        # Crear un nuevo profesor
        profesor3 = Profesor.objects.create_user(
            email="profesor3@test.com", nombre="Profesor Tres", password="password123"
        )

        # Crear una docencia para profesor3 con el mismo grupo y módulo que docencia1
        Docencia.objects.create(
            profesor=profesor3, grupo=self.grupo1, modulo=self.modulo1
        )

        # Autenticar como profesor3
        self.client.force_authenticate(user=profesor3)

        # Intentar acceder al seguimiento1 (del profesor1)
        url_detail = reverse("seguimiento-detail", args=[self.seguimiento1.id])
        response = self.client.get(url_detail)

        # Verificar que se permite el acceso
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EnviarRecordatorioSeguimientoViewTests(TestCase):
    """Tests for the email reminder functionality for follow-ups."""

    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = Profesor.objects.create_superuser(
            nombre="admin", email="admin@example.com", password="admin123"
        )

        # Create regular user (for permission testing)
        self.user = Profesor.objects.create_user(
            nombre="user", email="user@example.com", password="user123"
        )

        # Create test professors
        self.profesor_activo = Profesor.objects.create(
            nombre="Profesor Activo",
            email="profesor.activo@example.com",
            activo=True,
            is_active=True,
        )

        self.profesor_inactivo = Profesor.objects.create(
            nombre="Profesor Inactivo",
            email="profesor.inactivo@example.com",
            activo=False,
            is_active=True,
        )
        self.year = AñoAcademico.objects.create(año_academico="2023-24")
        self.ciclo = Ciclo.objects.create(año_academico=self.year, nombre="Ciclo 1")
        # Create test modules and groups
        self.modulo1 = Modulo.objects.create(
            nombre="Módulo 1", ciclo=self.ciclo, curso=2
        )
        self.modulo2 = Modulo.objects.create(
            nombre="Módulo 2", ciclo=self.ciclo, curso=2
        )

        self.grupo1 = Grupo.objects.create(nombre="Grupo A", ciclo=self.ciclo, curso=2)
        self.grupo2 = Grupo.objects.create(nombre="Grupo B", ciclo=self.ciclo, curso=2)

        # Create test docencias
        self.docencia1 = Docencia.objects.create(
            profesor=self.profesor_activo, modulo=self.modulo1, grupo=self.grupo1
        )

        self.docencia2 = Docencia.objects.create(
            profesor=self.profesor_activo, modulo=self.modulo2, grupo=self.grupo2
        )

        self.docencia3 = Docencia.objects.create(
            profesor=self.profesor_inactivo, modulo=self.modulo1, grupo=self.grupo2
        )

        # Set up API client
        self.client = APIClient()
        self.url = reverse("enviar-recordatorios")

        # Test data
        self.valid_payload = {
            "docencias": [self.docencia1.id, self.docencia2.id],
            "mes": 3,  # March
            "año_academico": "2025",
        }

        # Original settings backup
        self.original_frontend_url = getattr(
            settings, "FRONTEND_URL", "http://default-frontend.com"
        )
        settings.FRONTEND_URL = "http://test-frontend.com"

    def tearDown(self):
        """Clean up after tests."""
        # Restore settings
        settings.FRONTEND_URL = self.original_frontend_url

    def test_authentication_required(self):
        """Test that authentication is required."""
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_permission_required(self):
        """Test that admin permission is required."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_data(self):
        """Test validation of invalid input data."""
        self.client.force_authenticate(user=self.admin_user)

        # Missing required fields
        invalid_payload = {"docencias": [self.docencia1.id]}
        response = self.client.post(self.url, invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid month
        invalid_payload = {
            "docencias": [self.docencia1.id],
            "mes": 13,  # Invalid month
            "año_academico": "2025",
        }
        response = self.client.post(self.url, invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful_email_sending(self):
        """Test successful sending of reminder emails."""
        self.client.force_authenticate(user=self.admin_user)

        # Clear the mail outbox
        mail.outbox = []

        response = self.client.post(self.url, self.valid_payload, format="json")

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["emails_enviados"], 1)
        self.assertEqual(response.data["total_profesores"], 1)
        self.assertEqual(len(response.data["profesores_no_activos"]), 0)
        self.assertEqual(len(response.data["docencias_no_encontradas"]), 0)

        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        # Verify email content
        self.assertIn(
            f"Recordatorio de seguimiento pendiente - {calendar.month_name[3].capitalize()}",
            email.subject,
        )
        self.assertIn("Estimado/a Profesor Activo", email.body)
        self.assertIn("Módulo 1", email.body)
        self.assertIn("Módulo 2", email.body)
        self.assertIn("Grupo A", email.body)
        self.assertIn("Grupo B", email.body)
        self.assertIn(settings.FRONTEND_URL, email.body)
        self.assertEqual(email.to, ["profesor.activo@example.com"])

    def test_inactive_profesor(self):
        """Test that emails are not sent to inactive professors."""
        self.client.force_authenticate(user=self.admin_user)

        # Clear the mail outbox
        mail.outbox = []

        payload = {"docencias": [self.docencia3.id], "mes": 3, "año_academico": "2025"}

        response = self.client.post(self.url, payload, format="json")

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["emails_enviados"], 0)
        self.assertEqual(len(response.data["profesores_no_activos"]), 1)

        # Check no email was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_nonexistent_docencia(self):
        """Test handling of non-existent docencia IDs."""
        self.client.force_authenticate(user=self.admin_user)

        payload = {
            "docencias": [9999],  # Non-existent ID
            "mes": 3,
            "año_academico": "2025",
        }

        response = self.client.post(self.url, payload, format="json")

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["emails_enviados"], 0)
        self.assertEqual(len(response.data["docencias_no_encontradas"]), 1)
        self.assertEqual(response.data["docencias_no_encontradas"][0], 9999)

    def test_mixed_valid_invalid_docencias(self):
        """Test with a mix of valid and invalid docencia IDs."""
        self.client.force_authenticate(user=self.admin_user)

        # Clear the mail outbox
        mail.outbox = []

        payload = {
            "docencias": [self.docencia1.id, 9999],
            "mes": 3,
            "año_academico": "2025",
        }

        response = self.client.post(self.url, payload, format="json")

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["emails_enviados"], 1)
        self.assertEqual(len(response.data["docencias_no_encontradas"]), 1)

        # Check email was sent for valid docencia
        self.assertEqual(len(mail.outbox), 1)
