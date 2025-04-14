from django.urls import path, include
from rest_framework.routers import DefaultRouter
from seguimientos import views

router = DefaultRouter()
router.register(r"seguimientos", views.SeguimientoViewSet, basename="seguimiento")
router.register(r"modulos", views.ModuloViewSet, basename="modulo")
router.register(r"docencias", views.DocenciaViewSet, basename="docencia")
urlpatterns = [
    path("", include(router.urls)),
    path(
        "seguimientos-faltantes/<slug:año_academico>/<int:mes>/",
        views.SeguimientosFaltantesView.as_view(),
        name="seguimientos-faltantes",
    ),
    path(
        "api/seguimientos-faltantes-anual/<slug:año_academico>/",
        views.SeguimientosFaltantesAnualView.as_view(),
        name="seguimientos-faltantes-anual",
    ),
    path("year-actual/", views.CurrentAcademicYearView.as_view(), name="year-actual"),
    path(
        "enviar-recordatorios/",
        views.EnviarRecordatorioSeguimientoView.as_view(),
        name="enviar-recordatorios",
    ),
]
