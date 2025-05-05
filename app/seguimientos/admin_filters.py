from django.contrib import admin
from .utils import get_año_academico_actual
from .models import (
    AñoAcademico,
)


class BaseAñoAcademicoFilter(admin.SimpleListFilter):
    """
    Base filter for academic years that can be easily extended.

    To create a custom academic year filter, inherit from this class
    and override the get_filtered_queryset method.

    Example:
        class CustomAñoAcademicoFilter(BaseAñoAcademicoFilter):
            def get_filtered_queryset(self, queryset, año_academico):
                return queryset.filter(my_custom_field__año_academico=año_academico)
    """

    title = "año académico"
    parameter_name = "año_academico"

    def lookups(self, request, model_admin):
        # Get all distinct academic years
        años_academicos = AñoAcademico.objects.all().order_by("-año_academico")
        return [("todos", "Todos")] + [(año, año) for año in años_academicos]

    def choices(self, changelist):
        choices = list(super().choices(changelist))

        # If no filter is selected, select the current academic year by default
        if not self.value():
            # Get the current academic year
            año_actual = get_año_academico_actual()
            if año_actual:
                # Modify the default "All" option to be unselected
                choices[0]["selected"] = False

                # Add the current academic year as selected
                for choice in choices[1:]:
                    if str(choice["display"]) == str(año_actual):
                        choice["selected"] = True
                        break

        return choices

    def get_filtered_queryset(self, queryset, año_academico):
        """
        Apply filtering based on the academic year.
        Override this method in subclasses to customize filtering logic.

        Args:
            queryset: The original queryset to filter
            año_academico: The AñoAcademico instance to filter by

        Returns:
            Filtered queryset
        """
        return queryset.filter(docencia__modulo__ciclo__año_academico=año_academico)

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == "todos":
                return queryset
            # User has selected a value, get the corresponding AñoAcademico
            try:
                año_selected = AñoAcademico.objects.get(año_academico=self.value())
                return self.get_filtered_queryset(queryset, año_selected)
            except AñoAcademico.DoesNotExist:
                return queryset
        else:
            # No value selected, use current year
            año_actual = get_año_academico_actual()
            if año_actual:
                # Apply the filtering using the potentially overridden method
                return self.get_filtered_queryset(queryset, año_actual)

        # If no default or no value selected, return the complete queryset
        return queryset


class GrupoAndModuloAñoAcademicoFilter(BaseAñoAcademicoFilter):
    def get_filtered_queryset(self, queryset, año_academico):
        return queryset.filter(ciclo__año_academico=año_academico)


class CicloAñoAcademicoFilter(BaseAñoAcademicoFilter):
    def get_filtered_queryset(self, queryset, año_academico):
        return queryset.filter(año_academico=año_academico)
