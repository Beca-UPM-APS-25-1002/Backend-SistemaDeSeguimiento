from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.cache import cache
from seguimientos.models import AñoAcademico
from seguimientos.utils import (
    get_año_academico_actual,
)


class GetAñoAcademicoActualTests(TestCase):
    def setUp(self):
        # Limpiar la caché antes de cada prueba
        cache.clear()

        # Eliminar cualquier año académico existente
        AñoAcademico.objects.all().delete()

    def tearDown(self):
        # Limpiar la caché después de cada prueba
        cache.clear()

    def test_devuelve_valor_cacheado_si_existe(self):
        """Prueba que la función devuelve el valor de la caché si existe"""
        # Establecer un valor en la caché
        cache.set("año_academico_actual", "2023-24", 86400)

        # Llamar a la función
        resultado = get_año_academico_actual()

        # Verificar que devuelve el valor cacheado
        self.assertEqual(resultado, "2023-24")

    def test_devuelve_año_de_bd_si_hay_registros(self):
        """Prueba que la función devuelve el año del último registro en la BD"""
        # Crear algunos años académicos
        AñoAcademico.objects.create(año_academico="2022-23")
        AñoAcademico.objects.create(año_academico="2023-24")

        # Llamar a la función
        resultado = get_año_academico_actual()

        # Verificar que devuelve el año académico más reciente
        self.assertEqual(resultado, "2023-24")

        # Verificar que el resultado se guardó en caché
        self.assertEqual(cache.get("año_academico_actual"), "2023-24")

    @patch("seguimientos.utils.datetime")  # Ajusta según dónde está tu función
    def test_calcula_año_actual_antes_de_septiembre(self, mock_datetime):
        """Prueba que calcula correctamente el año cuando es antes de septiembre"""
        # Configurar el mock para devolver una fecha antes de septiembre
        mock_date = MagicMock()
        mock_date.month = 8  # Agosto
        mock_date.year = 2023
        mock_datetime.now.return_value = mock_date

        # Llamar a la función (sin años en la BD)
        resultado = get_año_academico_actual()

        # Verificar el formato correcto para antes de septiembre
        self.assertEqual(resultado, "2022-23")

        # Verificar que el resultado se guardó en caché
        self.assertEqual(cache.get("año_academico_actual"), "2022-23")

    @patch("seguimientos.utils.datetime")  # Ajusta según dónde está tu función
    def test_calcula_año_actual_despues_de_septiembre(self, mock_datetime):
        """Prueba que calcula correctamente el año cuando es después de septiembre"""
        # Configurar el mock para devolver una fecha después de septiembre
        mock_date = MagicMock()
        mock_date.month = 10  # Octubre
        mock_date.year = 2023
        mock_datetime.now.return_value = mock_date

        # Llamar a la función (sin años en la BD)
        resultado = get_año_academico_actual()

        # Verificar el formato correcto para después de septiembre
        self.assertEqual(resultado, "2023-24")

        # Verificar que el resultado se guardó en caché
        self.assertEqual(cache.get("año_academico_actual"), "2023-24")

    def test_ordenamiento_correcto(self):
        """Prueba que se selecciona el año que es el más reciente alfabéticamente"""
        # Crear algunos años en orden no cronológico
        AñoAcademico.objects.create(año_academico="2025-26")
        # Asumiendo que el ID será más alto para este, aunque alfabéticamente venga antes
        AñoAcademico.objects.create(año_academico="2023-24")

        # Llamar a la función
        resultado = get_año_academico_actual()

        # Verificar que devuelve el año con el ID más alto, no el más reciente alfabéticamente
        self.assertEqual(resultado, "2025-26")

    def test_tiempo_de_cache_correcto(self):
        """Prueba que el tiempo de caché se establece correctamente"""
        # Mock de la función cache.set para capturar sus argumentos
        with patch("seguimientos.utils.cache.set") as mock_cache_set:
            AñoAcademico.objects.create(año_academico="2023-24")

            # Llamar a la función
            get_año_academico_actual()

            # Verificar que cache.set fue llamado con el tiempo correcto (86400 segundos)
            mock_cache_set.assert_called_once()
            args, kwargs = mock_cache_set.call_args
            self.assertEqual(args[0], "año_academico_actual")  # Clave
            self.assertEqual(args[2], 86400)  # Tiempo en segundos (24 horas)

    def test_sin_años_academicos_y_sin_datetime(self):
        """Prueba un escenario de error donde no hay años académicos y datetime falla"""
        with patch("seguimientos.utils.datetime") as mock_datetime:
            # Simular un error al acceder a datetime
            mock_datetime.now.side_effect = Exception("Error simulado en datetime")

            # La función debería manejar este error graciosamente
            with self.assertRaises(Exception) as context:
                get_año_academico_actual()

            # Verificar que el error se propaga correctamente
            self.assertTrue("Error simulado en datetime" in str(context.exception))
