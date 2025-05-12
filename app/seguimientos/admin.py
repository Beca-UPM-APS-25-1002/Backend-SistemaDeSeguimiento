import calendar
from django.contrib.admin import SimpleListFilter
from dal import autocomplete
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin  # noqa: F401
from django.contrib.auth.models import Group
from django.forms import ModelForm
from django.shortcuts import render
from django.urls import path
from django.utils.html import format_html
from solo.admin import SingletonModelAdmin
from import_export import fields, resources
from import_export.admin import (
    ExportMixin,
)
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .admin_filters import (
    BaseAñoAcademicoFilter,
    GrupoAndModuloAñoAcademicoFilter,
    CicloAñoAcademicoFilter,
)
from .models import (
    AñoAcademico,
    Ciclo,
    Docencia,
    Grupo,
    Modulo,
    Profesor,
    Seguimiento,
    UnidadDeTrabajo,
    RecordatorioEmailConfig,
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
    list_display = ("año_academico", "actual", "get_clonar_button")

    def get_clonar_button(self, obj):
        """Añade un botón para clonar en cada fila"""
        url = reverse("admin:clonar_opciones", args=[obj.año_academico])
        return format_html(
            '<a class="btn btn-primary btn-sm" href="{}">Clonar</a>',
            url,
        )

    get_clonar_button.short_description = "Acciones"

    def get_urls(self):
        """Añade URLs personalizadas al admin"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/clonar/",
                self.admin_site.admin_view(self.clonar_opciones_view),
                name="clonar_opciones",
            ),
            path(
                "<path:object_id>/ejecutar_clonacion/",
                self.admin_site.admin_view(self.ejecutar_clonacion_view),
                name="ejecutar_clonacion",
            ),
        ]
        return custom_urls + urls

    def clonar_opciones_view(self, request, object_id):
        """Vista que muestra el formulario con opciones de clonación"""
        try:
            año_academico = AñoAcademico.objects.get(pk=object_id)
            context = {
                "año_academico": año_academico,
                "opts": self.model._meta,
                "title": f"Clonar año académico: {año_academico}",
                **self.admin_site.each_context(request),
            }
            return render(request, "admin/clonar_año.html", context)
        except AñoAcademico.DoesNotExist:
            self.message_user(request, "Año académico no encontrado", level="error")
            return HttpResponseRedirect(
                reverse("admin:seguimientos_añoacademico_changelist")
            )

    def ejecutar_clonacion_view(self, request, object_id):
        """Vista que procesa la clonación según las opciones seleccionadas"""
        if request.method != "POST":
            return HttpResponseRedirect(
                reverse("admin:clonar_opciones", args=[object_id])
            )

        try:
            año_academico_original = AñoAcademico.objects.get(pk=object_id)
            nuevo_año_valor = request.POST.get("nuevo_anio")
            opcion_clonacion = request.POST.get("opcion_clonacion")

            # Validar que el nuevo año no exista ya
            if AñoAcademico.objects.filter(año_academico=nuevo_año_valor).exists():
                self.message_user(
                    request,
                    f"El año académico {nuevo_año_valor} ya existe",
                    level="error",
                )
                return HttpResponseRedirect(
                    reverse("admin:clonar_opciones", args=[object_id])
                )

            # Crear el nuevo año académico
            nuevo_año = AñoAcademico(año_academico=nuevo_año_valor, actual=True)
            try:
                nuevo_año.full_clean()
            except ValidationError as err:
                self.message_user(
                    request,
                    err.messages[0],
                    level="error",
                )
                return HttpResponseRedirect(
                    reverse("admin:clonar_opciones", args=[object_id])
                )
            else:
                nuevo_año.save()

            # Lógica de clonación según la opción seleccionada
            if opcion_clonacion == "ciclos":
                self.clonar_ciclos(año_academico_original, nuevo_año)
                mensaje = f"Ciclos clonados al año académico {nuevo_año_valor}"
            elif opcion_clonacion == "modulos":
                self.clonar_modulos_y_grupos(año_academico_original, nuevo_año)
                mensaje = (
                    f"Ciclos y módulos clonados al año académico {nuevo_año_valor}"
                )
            elif opcion_clonacion == "docencias":
                self.clonar_docencias(año_academico_original, nuevo_año)
                mensaje = f"Ciclos, módulos y docencias clonados al año académico {nuevo_año_valor}"

            self.message_user(request, mensaje)
            return HttpResponseRedirect(
                reverse("admin:seguimientos_añoacademico_changelist")
            )

        except AñoAcademico.DoesNotExist:
            self.message_user(request, "Año académico no encontrado", level="error")
            return HttpResponseRedirect(
                reverse("admin:seguimientos_añoacademico_changelist")
            )
        except Exception as e:
            self.message_user(
                request, f"Error durante la clonación: {str(e)}", level="error"
            )
            return HttpResponseRedirect(
                reverse("admin:clonar_opciones", args=[object_id])
            )

    def clonar_ciclos(self, año_original, año_nuevo):
        """Clona los ciclos del año original al año nuevo"""
        ciclos_mapeados = {}
        ciclos_originales = Ciclo.objects.filter(año_academico=año_original)

        for ciclo in ciclos_originales:
            nuevo_ciclo = Ciclo.objects.create(
                nombre=ciclo.nombre, año_academico=año_nuevo
            )
            ciclos_mapeados[ciclo.id] = nuevo_ciclo

        return ciclos_mapeados

    def clonar_modulos_y_grupos(self, año_original, año_nuevo):
        """Clona ciclos y módulos"""
        ciclos_mapeados = self.clonar_ciclos(año_original, año_nuevo)
        modulos_mapeados = {}
        grupos_mapeados = {}
        # Clonar módulos
        modulos_originales = Modulo.objects.filter(ciclo__año_academico=año_original)
        for modulo in modulos_originales:
            nuevo_modulo = Modulo.objects.create(
                nombre=modulo.nombre,
                curso=modulo.curso,
                ciclo=ciclos_mapeados[modulo.ciclo_id],
            )
            modulos_mapeados[modulo.id] = nuevo_modulo

            # Clonar unidades de trabajo para cada módulo
            unidades = UnidadDeTrabajo.objects.filter(modulo=modulo)
            for unidad in unidades:
                UnidadDeTrabajo.objects.create(
                    numero_tema=unidad.numero_tema,
                    titulo=unidad.titulo,
                    modulo=nuevo_modulo,
                )

        # Clonar grupos
        for ciclo_original_id, ciclo_nuevo in ciclos_mapeados.items():
            grupos = Grupo.objects.filter(ciclo_id=ciclo_original_id)
            for grupo in grupos:
                grupo_nuevo = Grupo.objects.create(
                    nombre=grupo.nombre, ciclo=ciclo_nuevo, curso=grupo.curso
                )
                grupos_mapeados[grupo.id] = grupo_nuevo

        return modulos_mapeados, grupos_mapeados

    def clonar_docencias(self, año_original, año_nuevo):
        """Clona ciclos, módulos y docencias"""
        modulos_mapeados, grupos_mapeados = self.clonar_modulos_y_grupos(
            año_original, año_nuevo
        )

        # Clonar docencias
        docencias = Docencia.objects.filter(modulo__ciclo__año_academico=año_original)

        for docencia in docencias:
            if (
                docencia.modulo_id in modulos_mapeados
                and docencia.grupo_id in grupos_mapeados
            ):
                try:
                    Docencia.objects.create(
                        profesor=docencia.profesor,
                        grupo=grupos_mapeados[docencia.grupo_id],
                        modulo=modulos_mapeados[docencia.modulo_id],
                    )
                except Exception:
                    # Ignora errores de clave única si ya existe una docencia similar
                    pass


@admin.register(Ciclo)
class CicloAdmin(admin.ModelAdmin):
    list_display = ["nombre", "año_academico"]
    search_fields = ["nombre", "año_academico"]
    list_filter = [CicloAñoAcademicoFilter]
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
    list_filter = [GrupoAndModuloAñoAcademicoFilter, "ciclo", "curso"]
    search_fields = ["nombre", "ciclo__nombre"]


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "curso",
        "año_academico",
        "ciclo",
    ]
    list_filter = [
        GrupoAndModuloAñoAcademicoFilter,
        "ciclo",
        "curso",
    ]
    search_fields = ["nombre", "ciclo__nombre", "ciclo__año_academico"]
    inlines = [UnidadDeTrabajoInline, DocenciaInline]


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
        "modulo__ciclo__año_academico",
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
            "evaluacion",
            "temario_actual",
            "temario_completado",
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

    def dehydrate_temario_completado(self, obj):
        return ", ".join([str(unidad) for unidad in obj.temario_completado.all()])


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


# Create an inline for UnidadDeTrabajo within the Seguimiento admin
class TemarioCompletadoInline(admin.TabularInline):
    model = Seguimiento.temario_completado.through  # Use the through model
    extra = 1
    verbose_name = "Temario Completado"
    verbose_name_plural = "Temarios Completados"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filter temario based on docencia
        if (
            db_field.name == "unidaddetrabajo"
            and hasattr(self, "parent_obj")
            and self.parent_obj
        ):
            kwargs["queryset"] = UnidadDeTrabajo.objects.filter(
                modulo=self.parent_obj.docencia.modulo
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_formset(self, request, obj=None, **kwargs):
        # Store the parent object (modulo) for use in formfield_for_foreignkey
        self.parent_obj = obj
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields["unidaddetrabajo"].widget.can_add_related = False
        formset.form.base_fields["unidaddetrabajo"].widget.can_change_related = False
        formset.form.base_fields["unidaddetrabajo"].widget.can_view_related = False

        return formset


@admin.register(Seguimiento)
class SeguimientoAdmin(ExportMixin, admin.ModelAdmin):
    form = SeguimientoForm
    list_display = [
        "docencia",
        "get_mes",
        "get_estado_colored",
        "cumple_programacion",
        "temario_actual",
        "get_temario_completado",
    ]
    inlines = [TemarioCompletadoInline]

    # Custom filter for Modulo that depends on año_academico
    class ModuloFilter(SimpleListFilter):
        title = "módulo"
        parameter_name = "docencia__modulo"

        def lookups(self, request, model_admin):
            # Get the current año_academico filter value from the request
            año_academico = request.GET.get("año_academico", None)

            # Filter modules based on the selected año_academico
            if año_academico:
                modulos = Modulo.objects.filter(
                    ciclo__año_academico=año_academico
                ).distinct()
            else:
                modulos = Modulo.objects.all().distinct()

            return [(modulo.id, modulo) for modulo in modulos]

        def queryset(self, request, queryset):
            if self.value():
                return queryset.filter(docencia__modulo=self.value())
            return queryset

    list_filter = [
        "estado",
        "cumple_programacion",
        BaseAñoAcademicoFilter,
        "mes",
        ModuloFilter,
        "docencia__profesor",
    ]
    search_fields = [
        "docencia__profesor__nombre",
        "docencia__modulo__nombre",
        "docencia__grupo__nombre",
        "docencia__modulo__ciclo__año_academico",
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
                    "evaluacion",
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
        colors = {"ATRASADO": "red", "AL_DIA": "green", "ADELANTADO": "blue"}
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

    def get_temario_completado(self, obj):
        return ", ".join([str(unidad) for unidad in obj.temario_completado.all()])

    get_temario_completado.short_description = "Temario Completado"
    get_temario_completado.admin_order_field = "temario_completado"

    def get_form(self, request, obj=None, **kwargs):
        form = super(SeguimientoAdmin, self).get_form(request, obj, **kwargs)
        print(form.base_fields)
        form.base_fields["ultimo_contenido_impartido"].widget.can_add_related = False
        return form

    class Media:
        js = [
            "admin/js/vendor/jquery/jquery.min.js",
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

    actions = ["export_as_pdf"]

    def export_as_pdf(self, request, queryset):
        # Create a context with data for the template
        seguimientos = {}
        queryset_list = list(queryset)
        queryset_list.sort(key=lambda s: (str(s.año_academico), (s.mes + 3) % 12))
        for seguimiento in queryset_list:
            año = str(seguimiento.año_academico)
            mes = calendar.month_name[seguimiento.mes].title()

            if año not in seguimientos:
                seguimientos[año] = {}

            if mes not in seguimientos[año]:
                seguimientos[año][mes] = []

            seguimientos[año][mes].append(
                {
                    "id": seguimiento.id,
                    "profesor": seguimiento.profesor.nombre,
                    "modulo": seguimiento.modulo.nombre,
                    "grupo": seguimiento.grupo.nombre,
                    "ciclo": seguimiento.modulo.ciclo.nombre,
                    "año_academico": seguimiento.año_academico,
                    "mes": mes,
                    "evaluacion": seguimiento.get_evaluacion_display(),
                    "estado": seguimiento.get_estado_display(),
                    "temario_actual": str(seguimiento.temario_actual),
                    "ultimo_contenido_impartido": seguimiento.ultimo_contenido_impartido,
                    "cumple_programacion": "Sí"
                    if seguimiento.cumple_programacion
                    else "No",
                    "justificacion_estado": seguimiento.justificacion_estado,
                    "justificacion_cumple_programacion": seguimiento.justificacion_cumple_programacion,
                }
            )

        context = {
            "seguimientos": seguimientos,
            "count": len(queryset_list),
            "title": "Informe de Seguimientos",
        }

        # Render the template to HTML
        html_string = render_to_string("admin/seguimiento_pdf_export.html", context)

        # Generate PDF from HTML
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()

        # Create HTTP response with appropriate PDF headers
        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = (
            'attachment; filename="seguimientos_report.pdf"'
        )

        return response

    export_as_pdf.short_description = "Exportar seguimientos seleccionados a PDF"


@admin.register(RecordatorioEmailConfig)
class RecordatorioEmailConfigAdmin(SingletonModelAdmin):
    """
    Admin para configurar la plantilla de correo electrónico de recordatorio.
    """

    readonly_fields = ("help_text",)
    fieldsets = (
        (
            None,
            {
                "fields": ("asunto", "contenido"),
            },
        ),
        (
            "Ayuda",
            {
                "fields": ("help_text",),
                "classes": ("collapse",),
            },
        ),
    )
