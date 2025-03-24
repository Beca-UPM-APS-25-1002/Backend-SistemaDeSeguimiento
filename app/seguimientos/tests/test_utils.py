from django.test import TestCase
from django.core.cache import cache
from unittest.mock import patch
from seguimientos.utils import get_año_academico_actual
from seguimientos.models import Modulo, Ciclo


class ObtenerAñoAcademicoTests(TestCase):
    """
    Tests para la función get_año_academico_actual en utils.py
    """

    def setUp(self):
        """Configuración inicial para cada test"""
        # Limpiar la caché antes de cada prueba
        cache.clear()

        # Crear un ciclo para usar en las pruebas
        self.ciclo = Ciclo.objects.create(nombre="Desarrollo de Aplicaciones Web")

    def test_get_desde_cache(self):
        """Prueba que la función devuelve el valor de la caché si existe"""
        # Establecer un valor en la caché
        año_esperado = "2024-25"
        cache.set("año_academico_actual", año_esperado, 3600)

        # Obtener el año académico actual
        año_obtenido = get_año_academico_actual()

        # Verificar que se devolvió el valor de la caché
        self.assertEqual(año_obtenido, año_esperado)

    def test_get_desde_modulo_mas_reciente(self):
        """Prueba que la función obtiene el año del módulo más reciente"""
        # Crear varios módulos con diferentes años académicos
        Modulo.objects.create(
            nombre="Programación", curso=1, año_academico="2023-24", ciclo=self.ciclo
        )

        Modulo.objects.create(
            nombre="Bases de Datos", curso=1, año_academico="2024-25", ciclo=self.ciclo
        )

        # El módulo con ID más alto debería tener el año más reciente
        año_esperado = "2024-25"

        # Obtener el año académico actual
        año_obtenido = get_año_academico_actual()

        # Verificar que se devolvió el año del módulo más reciente
        self.assertEqual(año_obtenido, año_esperado)

        # Verificar que el valor se almacenó en caché
        self.assertEqual(cache.get("año_academico_actual"), año_esperado)

    def test_actualizacion_cache_despues_invalidacion(self):
        """Prueba que la caché se actualiza después de ser invalidada"""
        # Crear un módulo inicial
        Modulo.objects.create(
            nombre="Programación", curso=1, año_academico="2023-24", ciclo=self.ciclo
        )

        # Obtener el año académico para que se guarde en caché
        año_inicial = get_año_academico_actual()
        self.assertEqual(año_inicial, "2023-24")

        # Simular la invalidación de caché que ocurriría con el signal
        cache.delete("año_academico_actual")

        # Crear un nuevo módulo con un año más reciente
        Modulo.objects.create(
            nombre="Bases de Datos", curso=1, año_academico="2024-25", ciclo=self.ciclo
        )

        # Obtener de nuevo el año académico
        año_actualizado = get_año_academico_actual()

        # Verificar que se devolvió el nuevo año
        self.assertEqual(año_actualizado, "2024-25")

    def test_sin_modulos_valor_por_defecto(self):
        """Prueba el valor por defecto cuando no hay módulos"""
        # Asegurarse de que no hay módulos
        Modulo.objects.all().delete()

        # Si tu implementación actual devuelve un valor por defecto específico
        # cuando no hay módulos, ajusta esta prueba según corresponda
        try:
            año = get_año_academico_actual()
            # Verifica que el valor devuelto es del formato YYYY-YY
            self.assertRegex(año, r"^\d{4}-\d{2}$")
        except Exception as e:
            self.fail(f"La función falló con la excepción: {e}")
