from django.apps import AppConfig


class SeguimientosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "seguimientos"

    def ready(self):
        from django.contrib import admin
        from rest_framework.authtoken.models import (
            TokenProxy,
        )

        try:
            admin.site.unregister(TokenProxy)
        except admin.sites.NotRegistered:
            pass
        import locale

        locale.setlocale(locale.LC_ALL, "es_ES.UTF-8")
