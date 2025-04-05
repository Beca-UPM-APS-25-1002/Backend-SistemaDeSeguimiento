from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages

from seguimientos.models import (
    AñoAcademico,
    Ciclo,
    Docencia,
    Grupo,
    Modulo,
    Profesor,
    UnidadDeTrabajo,
)


class AñoAcademicoAdminTest(TestCase):
    """Test the AñoAcademico admin functionality, especially cloning."""

    def setUp(self):
        self.client = Client()
        self.admin_user = Profesor.objects.create_superuser(
            email="admin@example.com", password="adminpassword", nombre="Admin User"
        )
        self.client.login(email="admin@example.com", password="adminpassword")
        self.año_academico = AñoAcademico.objects.create(año_academico="2022-23")

        # Create a test ciclo
        self.ciclo = Ciclo.objects.create(
            nombre="DAW", año_academico=self.año_academico
        )

        # Create test modulos
        self.modulo = Modulo.objects.create(
            nombre="Programación", curso=1, ciclo=self.ciclo
        )

        # Create test unidades de trabajo
        self.unidad = UnidadDeTrabajo.objects.create(
            numero_tema=1, titulo="Introducción a Python", modulo=self.modulo
        )

        # Create test grupo
        self.grupo = Grupo.objects.create(nombre="1DAW", ciclo=self.ciclo, curso=1)

        # Create test profesor
        self.profesor = Profesor.objects.create_user(
            email="profesor@example.com", password="password", nombre="Profesor Test"
        )

        # Create test docencia
        self.docencia = Docencia.objects.create(
            profesor=self.profesor, modulo=self.modulo, grupo=self.grupo
        )

    def test_year_cloning_view_access(self):
        """Test that the cloning options view is accessible."""
        url = reverse("admin:clonar_opciones", args=[self.año_academico.año_academico])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Clonar año académico: {self.año_academico}")

    def test_clone_cycles_only(self):
        """Test cloning only cycles to a new academic year."""
        url = reverse(
            "admin:ejecutar_clonacion", args=[self.año_academico.año_academico]
        )
        response = self.client.post(
            url, {"nuevo_anio": "2023-24", "opcion_clonacion": "ciclos"}
        )

        # Check redirection
        self.assertEqual(response.status_code, 302)

        # Check new year was created
        self.assertTrue(AñoAcademico.objects.filter(año_academico="2023-24").exists())

        # Check ciclos were cloned
        nuevo_año = AñoAcademico.objects.get(año_academico="2023-24")
        self.assertEqual(Ciclo.objects.filter(año_academico=nuevo_año).count(), 1)

        # Check modulos were not cloned
        ciclo_clonado = Ciclo.objects.get(año_academico=nuevo_año)
        self.assertEqual(Modulo.objects.filter(ciclo=ciclo_clonado).count(), 0)

    def test_clone_modules_and_groups(self):
        """Test cloning cycles, modules and groups to a new academic year."""
        url = reverse(
            "admin:ejecutar_clonacion", args=[self.año_academico.año_academico]
        )
        response = self.client.post(
            url, {"nuevo_anio": "2023-24", "opcion_clonacion": "modulos"}
        )

        # Check redirection
        self.assertEqual(response.status_code, 302)

        # Check new year was created
        nuevo_año = AñoAcademico.objects.get(año_academico="2023-24")

        # Check ciclos were cloned
        ciclo_clonado = Ciclo.objects.get(año_academico=nuevo_año)

        # Check modulos were cloned
        self.assertEqual(Modulo.objects.filter(ciclo=ciclo_clonado).count(), 1)

        # Check unidades de trabajo were cloned
        modulo_clonado = Modulo.objects.get(ciclo=ciclo_clonado)
        self.assertEqual(
            UnidadDeTrabajo.objects.filter(modulo=modulo_clonado).count(), 1
        )

        # Check grupos were cloned
        self.assertEqual(Grupo.objects.filter(ciclo=ciclo_clonado).count(), 1)

        # Check docencias were NOT cloned
        self.assertEqual(Docencia.objects.filter(modulo=modulo_clonado).count(), 0)

    def test_clone_with_docencias(self):
        """Test cloning everything including docencias to a new academic year."""
        url = reverse(
            "admin:ejecutar_clonacion", args=[self.año_academico.año_academico]
        )
        response = self.client.post(
            url, {"nuevo_anio": "2023-24", "opcion_clonacion": "docencias"}
        )

        # Check redirection
        self.assertEqual(response.status_code, 302)

        # Check new year was created
        nuevo_año = AñoAcademico.objects.get(año_academico="2023-24")

        # Check ciclos were cloned
        ciclo_clonado = Ciclo.objects.get(año_academico=nuevo_año)

        # Check modulos were cloned
        modulo_clonado = Modulo.objects.get(ciclo=ciclo_clonado)

        # Check grupos were cloned
        grupo_clonado = Grupo.objects.get(ciclo=ciclo_clonado)

        # Check docencias were cloned
        self.assertEqual(
            Docencia.objects.filter(
                modulo=modulo_clonado, grupo=grupo_clonado, profesor=self.profesor
            ).count(),
            1,
        )

    def test_duplicate_year_validation(self):
        """Test validation prevents creating a duplicate academic year."""
        url = reverse(
            "admin:ejecutar_clonacion", args=[self.año_academico.año_academico]
        )
        response = self.client.post(
            url,
            {
                "nuevo_anio": "2022-23",  # Same as existing year
                "opcion_clonacion": "ciclos",
            },
        )

        # Should redirect back to options view
        self.assertEqual(response.status_code, 302)

        # Get messages
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("ya existe", str(messages[0]))


class ProfesorAdminTest(TestCase):
    """Test the custom profesor admin with is_admin toggle."""

    def setUp(self):
        self.client = Client()
        self.admin_user = Profesor.objects.create_superuser(
            email="admin@example.com", password="adminpassword", nombre="Admin User"
        )
        self.client.login(email="admin@example.com", password="adminpassword")

        self.normal_profesor = Profesor.objects.create_user(
            email="profesor@example.com",
            password="password",
            nombre="Profesor Normal",
            is_admin=False,
            is_staff=False,
            is_superuser=False,
        )

    def test_admin_toggle_updates_permissions(self):
        """Test that toggling the es_admin field updates all permission fields."""
        url = reverse(
            "admin:seguimientos_profesor_change", args=[self.normal_profesor.id]
        )

        # Get the change form
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Submit the form with es_admin checked
        response = self.client.post(
            url,
            {
                "email": "profesor@example.com",
                "nombre": "Profesor Normal",
                "activo": True,
                "es_admin": True,
                "password": self.normal_profesor.password,  # Don't change password
            },
        )

        # Check redirection
        self.assertEqual(response.status_code, 302)

        # Refresh from DB
        self.normal_profesor.refresh_from_db()

        # Check permissions were updated
        self.assertTrue(self.normal_profesor.is_admin)
        self.assertTrue(self.normal_profesor.is_staff)
        self.assertTrue(self.normal_profesor.is_superuser)
