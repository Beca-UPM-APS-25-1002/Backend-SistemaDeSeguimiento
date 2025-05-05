from django.test import TestCase
from django.core.cache import cache
from seguimientos.models import AñoAcademico
from seguimientos.utils import (
    get_año_academico_actual,
)


class GetAñoAcademicoActualTests(TestCase):
    """Tests para la función get_año_academico_actual"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Limpiar la caché antes de cada test
        cache.clear()

    def test_get_año_con_actual_definido(self):
        """Probar que devuelve el año marcado como actual"""
        # Crear varios años
        AñoAcademico.objects.create(año_academico="2022-23")
        AñoAcademico.objects.create(año_academico="2023-24", actual=True)
        AñoAcademico.objects.create(año_academico="2024-25")

        # Verificar que se devuelve el año actual
        self.assertEqual(get_año_academico_actual(), "2023-24")

    def test_caché_funciona(self):
        """Probar que el resultado se guarda en caché"""
        # Crear un año actual
        AñoAcademico.objects.create(año_academico="2023-24", actual=True)

        # Llamar a la función para que guarde en caché
        get_año_academico_actual()

        # Verificar que el valor está en caché
        self.assertEqual(cache.get("año_academico_actual"), "2023-24")

        # Cambiar el año actual
        año_obj = AñoAcademico.objects.get(actual=True)
        año_obj.año_academico = "2024-25"
        año_obj.save()

        # La función debería devolver el valor actualizado
        self.assertEqual(get_año_academico_actual(), "2024-25")

        # Limpiar la caché y verificar que devuelve el valor actualizado
        cache.clear()
        self.assertEqual(get_año_academico_actual(), "2024-25")
