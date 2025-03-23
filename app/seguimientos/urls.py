from django.urls import path, include
from rest_framework.routers import DefaultRouter
from seguimientos import views

router = DefaultRouter()
router.register(r"seguimientos", views.SeguimientoViewSet, basename="seguimiento")
router.register(r"modulos", views.ModuloViewSet, basename="modulo")
urlpatterns = [
    path("", include(router.urls)),
    path(
        "seguimientos-faltantes/<slug:año_academico>/<int:mes>/",
        views.SeguimientosFaltantesView.as_view(),
        name="seguimientos-faltantes",
    ),
    path("current-year/", views.CurrentAcademicYearView.as_view(), name="current-year"),
]
