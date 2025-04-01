import calendar

from dal import autocomplete
from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin  # noqa: F401
from django.contrib.auth.models import Group
from django.forms import ModelForm
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.html import format_html
from import_export import fields, resources
from import_export.admin import ExportMixin

from .models import (
    AñoAcademico,
    Ciclo,
    Docencia,
    Grupo,
    Modulo,
    Profesor,
    Seguimiento,
    UnidadDeTrabajo,
)

admin.site.site_header = "Administración de Seguimientos"
admin.site.site_title = "Administración de Seguimientos"
admin.site.index_title = (
    "Bienvenido al portal administrativo del sistema de seguimientos"
)
admin.site.unregister(Group)


class DocenciaInline(admin.TabularInline):
    model = Docencia
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filter grupos based on modulo's ciclo
        if db_field.name == "grupo" and hasattr(self, "parent_obj") and self.parent_obj:
            kwargs["queryset"] = Grupo.objects.filter(
                ciclo=self.parent_obj.ciclo, curso=self.parent_obj.curso
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_formset(self, request, obj=None, **kwargs):
        # Store the parent object (modulo) for use in formfield_for_foreignkey
        self.parent_obj = obj
        return super().get_formset(request, obj, **kwargs)


class GrupoInline(admin.TabularInline):
    model = Grupo
    extra = 1


class ModuloInline(admin.TabularInline):
    model = Modulo
    extra = 1
    fields = ["nombre", "curso"]


@admin.register(AñoAcademico)
class AñoAcademicoAdmin(admin.ModelAdmin):
    list_display = ["año_academico"]


@admin.register(Ciclo)
class CicloAdmin(admin.ModelAdmin):
    list_display = ["nombre", "año_academico"]
    search_fields = ["nombre", "año_academico"]
    list_filter = ["año_academico"]
    inlines = [GrupoInline, ModuloInline]


class UnidadDeTrabajoInline(admin.TabularInline):
    model = UnidadDeTrabajo
    extra = 1
    fields = [
        "numero_tema",
        "titulo",
    ]
    ordering = ("numero_tema",)


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "ciclo", "curso"]
    list_filter = ["ciclo", "curso"]
    search_fields = ["nombre", "ciclo__nombre"]


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "curso",
        "año_academico",
        "ciclo",
    ]
    list_filter = ["ciclo__año_academico", "curso", "ciclo"]
    search_fields = ["nombre", "ciclo__nombre", "ciclo__año_academico"]
    actions = ["duplicar_modulos"]
    inlines = [UnidadDeTrabajoInline, DocenciaInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "duplicar_modulos/",
                self.admin_site.admin_view(self.duplicar_modulos_view),
                name="duplicar_modulos",
            ),
        ]
        return custom_urls + urls

    def duplicar_modulos(self, request, queryset):
        """Redirige a la página de selección de año académico."""
        if not queryset.exists():
            self.message_user(
                request, "No has seleccionado ningún módulo.", level=messages.WARNING
            )
            return redirect("/admin/seguimientos/modulo/")

        # Guardamos en la sesión los IDs de los módulos seleccionados
        request.session["modulos_a_duplicar"] = list(
            queryset.values_list("id", flat=True)
        )
        return redirect("/admin/seguimientos/modulo/duplicar_modulos/")

    duplicar_modulos.short_description = "Duplicar módulos a otro año"

    def duplicar_modulos_view(self, request):
        """Vista personalizada para introducir el nuevo año académico."""
        modulos_ids = request.session.get("modulos_a_duplicar", [])
        if not modulos_ids:
            messages.error(request, "No has seleccionado ningún módulo para duplicar.")
            return redirect("/admin/seguimientos/modulo/")

        modulos = Modulo.objects.filter(id__in=modulos_ids)

        if request.method == "POST":
            nuevo_anio = request.POST.get("nuevo_anio")
            if not nuevo_anio:
                messages.error(request, "Debes ingresar un año académico válido.")
                return redirect("/admin/seguimientos/modulo/duplicar_modulos/")

            for modulo in modulos:
                nuevo_modulo = Modulo.objects.create(
                    nombre=modulo.nombre,
                    curso=modulo.curso,
                    año_academico=nuevo_anio,
                    ciclo=modulo.ciclo,
                )
                # Clonar las Unidades de Temario
                unidades = UnidadDeTrabajo.objects.filter(modulo=modulo)
                for unidad in unidades:
                    UnidadDeTrabajo.objects.create(
                        numero_tema=unidad.numero_tema,
                        titulo=unidad.titulo,
                        impartido=False,
                        modulo=nuevo_modulo,
                    )

            messages.success(
                request, f"Se duplicaron {modulos.count()} módulos al año {nuevo_anio}."
            )
            return redirect("/admin/seguimientos/modulo/")

        return render(request, "admin/duplicar_modulos.html", {"modulos": modulos})


@admin.register(UnidadDeTrabajo)
class UnidadDeTrabajoAdmin(admin.ModelAdmin):
    list_display = [
        "numero_tema",
        "titulo",
        "modulo",
        "año_academico",
    ]
    list_filter = ["modulo"]
    search_fields = ["titulo", "modulo__nombre"]

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}


class ProfesorForm(ModelForm):
    """Formulario que añade un solo toggle para hacer administrador a un profesor."""

    es_admin = forms.BooleanField(
        label="Es Administrador",
        required=False,
        help_text="Activa esta opción para dar permisos de administrador.",
    )

    class Meta:
        model = Profesor
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer el valor del toggle basado en los permisos actuales
        if self.instance:
            self.fields["es_admin"].initial = self.instance.is_admin

    def save(self, commit=True):
        """Guarda el estado de administrador y ajusta los permisos."""
        instance = super().save(commit=False)
        es_admin = self.cleaned_data.get("es_admin", False)

        # Modificar los permisos con un solo toggle
        instance.is_admin = es_admin
        instance.is_staff = es_admin
        instance.is_superuser = es_admin

        if commit:
            instance.save()
        return instance


class ProfesorAdmin(admin.ModelAdmin):
    form = ProfesorForm  # Usa el formulario personalizado
    list_display = ["nombre", "email", "activo", "es_admin"]
    list_filter = ["activo", "is_admin"]
    search_fields = ["nombre", "email"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información Personal", {"fields": ("nombre", "activo")}),
        (
            "Permisos",
            {"fields": ("es_admin",)},
        ),
    )

    @admin.display(boolean=True, description="Administrador")
    def es_admin(self, obj):
        return obj.is_admin


admin.site.register(Profesor, ProfesorAdmin)


@admin.register(Docencia)
class DocenciaAdmin(admin.ModelAdmin):
    list_display = ["profesor", "modulo", "grupo", "get_año_academico"]
    list_filter = ["modulo__ciclo__año_academico", "grupo"]
    search_fields = [
        "profesor__nombre",
        "modulo__nombre",
        "modulo__año_academico",
        "grupo__nombre",
    ]
    autocomplete_fields = ["profesor", "grupo", "modulo"]

    def get_año_academico(self, obj):
        return obj.año_academico

    get_año_academico.short_description = "Año Académico"
    get_año_academico.admin_order_field = "modulo__ciclo__año_academico"

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}


class SeguimientoResource(resources.ModelResource):
    profesor = fields.Field(
        column_name="Profesor", attribute="docencia__profesor__nombre"
    )
    mes = fields.Field(column_name="Mes", attribute="mes")
    ciclo = fields.Field(column_name="Ciclo", attribute="docencia__modulo__ciclo")
    nombre_modulo = fields.Field(
        column_name="Modulo", attribute="docencia__modulo__nombre"
    )
    grupo = fields.Field(column_name="Grupo", attribute="docencia__grupo__nombre")
    temario_actual = fields.Field(column_name="Temario Alcanzado")
    cumple_programacion = fields.Field(column_name="Cumple Programación")

    class Meta:
        model = Seguimiento
        fields = [
            "profesor",
            "ciclo",
            "nombre_modulo",
            "grupo",
            "mes",
            "temario_actual",
            "temario_actual",
            "ultimo_contenido_impartido",
            "estado",
            "justificacion_estado",
            "cumple_programacion",
            "justificacion_cumple_programacion",
        ]

    def dehydrate_mes(self, obj):
        return calendar.month_name[obj.mes].capitalize()

    def dehydrate_temario_actual(self, obj):
        return f"{obj.temario_actual}"

    def dehydrate_cumple_programacion(self, obj):
        return "Sí" if obj.cumple_programacion else "No"


class SeguimientoForm(forms.ModelForm):
    class Meta:
        model = Seguimiento
        fields = "__all__"
        widgets = {
            "temario_actual": autocomplete.ModelSelect2(
                url="/admin/seguimientos/seguimiento/temario-autocomplete",
                forward=["docencia"],
            ),
        }


@admin.register(Seguimiento)
class SeguimientoAdmin(ExportMixin, admin.ModelAdmin):
    form = SeguimientoForm
    list_display = [
        "docencia",
        "get_mes",
        "get_estado_colored",
        "cumple_programacion",
        "temario_actual",
    ]
    list_filter = [
        "estado",
        "cumple_programacion",
        "mes",
        "docencia__modulo__ciclo__año_academico",
    ]
    search_fields = [
        "docencia__profesor__nombre",
        "docencia__modulo__nombre",
        "docencia__grupo__nombre",
    ]
    autocomplete_fields = ["docencia", "temario_actual"]
    resource_classes = [SeguimientoResource]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "docencia",
                    "mes",
                    "temario_actual",
                    "ultimo_contenido_impartido",
                )
            },
        ),
        ("Estado del Seguimiento", {"fields": ("estado", "justificacion_estado")}),
        (
            "Cumplimiento de la Programación",
            {"fields": ("cumple_programacion", "justificacion_cumple_programacion")},
        ),
    )

    def get_estado_colored(self, obj):
        colors = {"ATRASADO": "red", "AL_DIA": "green", "ADELANTADO": "aqua"}
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.estado, "black"),
            obj.get_estado_display(),
        )

    get_estado_colored.short_description = "Estado"
    get_estado_colored.admin_order_field = "estado"

    def get_mes(self, obj):
        return calendar.month_name[obj.mes].capitalize()

    get_mes.short_description = "Mes"
    get_mes.admin_order_field = "mes"

    class Media:
        js = [
            "admin/js/vendor/jquery/jquery.min.js",
            "autocomplete_light/jquery.init.js",
            "autocomplete_light/autocomplete.init.js",
        ]
        css = {
            "all": [
                "admin/css/vendor/select2/select2.min.css",
                "autocomplete_light/select2.css",
            ],
        }

    class TemarioAutocomplete(autocomplete.Select2QuerySetView):
        def get_queryset(self):
            qs = UnidadDeTrabajo.objects.all().order_by("numero_tema")

            # Get the docencia from the forwarded value
            docencia = self.forwarded.get("docencia", None)
            if docencia:
                try:
                    # Filter by the selected docencia's modulo
                    docencia_obj = Docencia.objects.get(pk=docencia)
                    qs = qs.filter(modulo=docencia_obj.modulo)
                except Docencia.DoesNotExist:
                    return UnidadDeTrabajo.objects.none()
            else:
                return UnidadDeTrabajo.objects.none()

            if self.q:
                qs = qs.filter(titulo__icontains=self.q)

            return qs

        def get_result_label(self, item):
            return f"T{item.numero_tema} - {item.titulo}"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "temario-autocomplete/",
                self.TemarioAutocomplete.as_view(),
                name="temario-autocomplete",
            ),
        ]
        return custom_urls + urls
