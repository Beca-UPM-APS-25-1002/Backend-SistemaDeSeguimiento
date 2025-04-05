from django.core.exceptions import ValidationError
import re


def validate_año(year):
    """Metodo que valida que el año tenga el formato yyyy-yy donde el segundo año es 1 más que el primero"""
    if re.match(r"^\d{4}-\d{2}$", year) is None:
        raise ValidationError(f"{year} no tiene el formato yyyy-yy")
    year_splitted = year.split("-")
    if (int(year_splitted[0]) + 1) % 100 != int(year_splitted[1]) % 100:
        raise ValidationError(
            f"En {year}, {year_splitted[1]} no es el año siguiente a {year_splitted[0]}"
        )
