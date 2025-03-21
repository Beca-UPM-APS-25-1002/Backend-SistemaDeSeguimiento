from django.urls import path, include
from rest_framework.routers import DefaultRouter
from seguimientos import views

router = DefaultRouter()
router.register(r"seguimientos", views.SeguimientoViewSet, basename="seguimiento")
urlpatterns = [path("", include(router.urls))]
