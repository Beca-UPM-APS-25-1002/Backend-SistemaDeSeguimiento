from django.core.cache import cache
from .models import Modulo


def obtener_año_academico_actual():
    """
    Devuelve el año académico del módulo más reciente (con el ID más alto)
    con caché para minimizar las consultas a la base de datos.
    """
    # Comprobar si tenemos un valor en caché
    clave_cache = "año_academico_actual"
    año_cacheado = cache.get(clave_cache)

    if año_cacheado:
        return año_cacheado

    # Obtener el módulo con el ID más alto (el más reciente)
    modulo_mas_reciente = Modulo.objects.order_by("-id").first()

    if modulo_mas_reciente:
        ultimo_año = modulo_mas_reciente.año_academico
    else:
        # Si no hay módulos, usar la lógica del año actual como respaldo
        from datetime import datetime

        fecha_actual = datetime.now()
        mes_actual = fecha_actual.month
        año_actual = fecha_actual.year

        if mes_actual < 9:  # Antes de septiembre
            ultimo_año = f"{año_actual - 1}-{str(año_actual)[2:]}"
        else:
            ultimo_año = f"{año_actual}-{str(año_actual + 1)[2:]}"

    # Almacenar el resultado en caché (86400 segundos = 24 horas)
    cache.set(clave_cache, ultimo_año, 86400)

    return ultimo_año
