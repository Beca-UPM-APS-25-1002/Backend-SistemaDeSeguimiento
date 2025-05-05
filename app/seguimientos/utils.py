from django.core.cache import cache
from .models import AñoAcademico


def get_año_academico_actual():
    """
    Devuelve el año académico actual
    con caché para minimizar las consultas a la base de datos.
    """
    # Comprobar si tenemos un valor en caché
    clave_cache = "año_academico_actual"
    año_cacheado = cache.get(clave_cache)

    if año_cacheado:
        return año_cacheado

    # Obtener el year actual
    latest_year = AñoAcademico.objects.filter(actual=True).first()

    if latest_year:
        ultimo_año = latest_year.año_academico
        # Almacenar el resultado en caché (86400 segundos = 24 horas)
        cache.set(clave_cache, ultimo_año, 86400)
    else:
        ultimo_año = ""

    return ultimo_año
