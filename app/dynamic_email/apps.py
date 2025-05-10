from django.apps import AppConfig


class DynamicEmailConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dynamic_email"
    verbose_name = "Configuración de correo"
