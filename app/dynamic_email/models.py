from django.db import models
from solo.models import SingletonModel


class EmailSettings(SingletonModel):
    """
    Singleton model that stores email configuration settings.
    Uses django-solo to ensure only one instance of this model exists.
    """

    email_host = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text="El servidor que se utilizará para enviar correo electrónico.",
    )
    email_port = models.IntegerField(
        default=587, help_text="Puerto a utilizar para el servidor SMTP."
    )
    email_host_user = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text="Nombre de usuario para el servidor SMTP.",
    )
    email_host_password = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text="Contraseña para el servidor SMTP.",
    )
    email_use_tls = models.BooleanField(
        default=True, help_text="Si se debe usar una conexión TLS."
    )
    email_use_ssl = models.BooleanField(
        default=False, help_text="Si se debe usar una conexión SSL implícita."
    )
    email_fail_silently = models.BooleanField(
        default=False,
        help_text="Si los errores deben ser silenciosos al enviar correo.",
    )
    email_timeout = models.IntegerField(
        default=60,
        help_text="Tiempo de espera en segundos para operaciones de bloqueo.",
    )

    class Meta:
        verbose_name = "Configuración de Correo"

    def __str__(self):
        return "Configuración de Correo"
