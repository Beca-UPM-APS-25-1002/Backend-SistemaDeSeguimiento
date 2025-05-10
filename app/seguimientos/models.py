from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.functional import cached_property
from django.core.cache import cache
from solo.models import SingletonModel
from django.core.exceptions import ValidationError

from .validators import validate_año


class AñoAcademico(models.Model):
    año_academico = models.CharField(
        null=False, max_length=7, primary_key=True, validators=[validate_año]
    )
    actual = models.BooleanField(default=False)

    def __str__(self):
        return self.año_academico

    def save(self, *args, **kwargs):
        """Invalidamos el cache de años si se ha registrado un nuevo modulo"""
        # Comprobamos si este es el primer registro creado
        if not AñoAcademico.objects.exists():
            self.actual = True
        elif self.actual:
            # Si esta instancia se establece como actual, ponemos todas las demás como False
            AñoAcademico.objects.exclude(pk=self.pk).update(actual=False)

        cache.delete("año_academico_actual")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Si eliminamos el año actual, establecemos el año más alto como actual"""
        is_actual = self.actual

        # Llamamos primero al método delete del padre
        super().delete(*args, **kwargs)

        # Después de la eliminación, si este era el año actual, establecemos el año más alto como actual
        if is_actual and AñoAcademico.objects.exists():
            highest_year = AñoAcademico.objects.order_by("-año_academico").first()
            if highest_year:
                highest_year.actual = True
                highest_year.save()

    class Meta:
        verbose_name = "Año Academico"
        verbose_name_plural = "Años Academicos"


class Ciclo(models.Model):
    nombre = models.CharField(null=False, max_length=255)
    año_academico = models.ForeignKey(
        AñoAcademico,
        on_delete=models.CASCADE,
        to_field="año_academico",
        related_name="ciclos",
    )

    def __str__(self):
        return f"{self.nombre} - {self.año_academico}"

    class Meta:
        ordering = ["-año_academico", "nombre"]


class Grupo(models.Model):
    nombre = models.CharField(null=False, max_length=255)
    ciclo = models.ForeignKey(Ciclo, on_delete=models.CASCADE, related_name="grupos")
    curso = models.IntegerField(null=False, validators=[MinValueValidator(1)])

    @cached_property
    def año_academico(self):
        return self.ciclo.año_academico

    def __str__(self):
        return f"{self.nombre} - {self.ciclo}"

    class Meta:
        ordering = ["-ciclo__año_academico", "nombre"]


class Modulo(models.Model):
    nombre = models.CharField(null=False, max_length=255)
    curso = models.IntegerField(null=False, validators=[MinValueValidator(1)])
    ciclo = models.ForeignKey(Ciclo, on_delete=models.CASCADE, related_name="modulos")

    @cached_property
    def año_academico(self):
        return self.ciclo.año_academico

    def __str__(self):
        return f"{self.nombre} - {self.ciclo}"

    class Meta:
        indexes = [
            models.Index(fields=["ciclo"]),
        ]
        ordering = ["-ciclo__año_academico", "ciclo", "curso", "nombre"]


class UnidadDeTrabajo(models.Model):
    numero_tema = models.IntegerField(null=False, validators=[MinValueValidator(1)])
    titulo = models.CharField(max_length=255, null=False)
    modulo = models.ForeignKey(
        Modulo, on_delete=models.CASCADE, related_name="unidades_de_temario"
    )

    @cached_property
    def año_academico(self):
        return self.modulo.ciclo.año_academico

    def __str__(self):
        return f"T{self.numero_tema} - {self.titulo}"

    class Meta:
        verbose_name = "Unidad de Temario"
        verbose_name_plural = "Unidades de Temario"
        ordering = ["numero_tema"]
        constraints = [
            models.UniqueConstraint(fields=["numero_tema", "modulo"], name="tema_unico")
        ]


class ProfesorManager(BaseUserManager):
    def create_user(self, email, nombre, password=None, **extra_fields):
        if not email:
            raise ValueError("Los usuarios deben tener un email válido")
        if not nombre:
            raise ValueError("Los profesores deben tener un nombre")
        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_admin", True)

        return self.create_user(email, nombre, password, **extra_fields)


class Profesor(AbstractUser):
    username = None  # Remove username field
    email = models.EmailField(unique=True, null=False)
    nombre = models.CharField(max_length=255, null=False)
    activo = models.BooleanField(default=True)

    # Fields required by Django
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    # Fix for related_name clashes
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        related_name="profesor_set",
        related_query_name="profesor",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        related_name="profesor_set",
        related_query_name="profesor",
    )

    objects = ProfesorManager()

    USERNAME_FIELD = "email"  # Usar email en vez de username
    REQUIRED_FIELDS = ["nombre"]  # Campos requeridos de superuser

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        """Hasheamos la contraseña en caso de que no haya sido hasheada"""
        if self.password and not self.password.startswith(
            ("pbkdf2_sha256$", "bcrypt$", "argon2")
        ):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Profesor"
        verbose_name_plural = "Profesores"


class Docencia(models.Model):
    profesor = models.ForeignKey(
        Profesor, on_delete=models.CASCADE, related_name="docencias"
    )
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="docencias")
    modulo = models.ForeignKey(
        Modulo, on_delete=models.CASCADE, related_name="docencias"
    )

    @cached_property
    def año_academico(self):
        return self.modulo.ciclo.año_academico

    class Meta:
        # Garantizar que un profesor no sea asignado al mismo módulo y grupo dos veces en el mismo curso académico.
        unique_together = ["profesor", "grupo", "modulo"]
        indexes = [
            models.Index(fields=["profesor", "modulo"]),
            models.Index(fields=["grupo", "modulo"]),
        ]

    def __str__(self):
        return f"{self.profesor.nombre} - {self.modulo.nombre} ({self.modulo.ciclo.año_academico}) - {self.grupo.nombre}"


class EstadoSeguimiento(models.TextChoices):
    ATRASADO = "ATRASADO", "Atrasado"
    AL_DIA = "AL_DIA", "Al día"
    ADELANTADO = "ADELANTADO", "Adelantado"


class EvaluacionSeguimiento(models.TextChoices):
    PRIMERA = "PRIMERA", "Primera"
    SEGUNDA = "SEGUNDA", "Segunda"
    TERCERA = "TERCERA", "Tercera"


class Seguimiento(models.Model):
    temario_actual = models.ForeignKey(
        UnidadDeTrabajo, on_delete=models.RESTRICT, related_name="seguimientos"
    )
    ultimo_contenido_impartido = models.CharField(max_length=255)
    estado = models.CharField(
        max_length=10,
        choices=EstadoSeguimiento.choices,
        default=EstadoSeguimiento.AL_DIA,
    )
    justificacion_estado = models.CharField(max_length=255, blank=True)
    cumple_programacion = models.BooleanField(default=True)
    justificacion_cumple_programacion = models.CharField(max_length=255, blank=True)
    mes = models.IntegerField(validators=[MaxValueValidator(12), MinValueValidator(1)])
    docencia = models.ForeignKey(
        Docencia, on_delete=models.CASCADE, related_name="seguimientos"
    )
    evaluacion = models.CharField(
        choices=EvaluacionSeguimiento.choices, blank=False, null=False
    )

    @cached_property
    def año_academico(self):
        return self.docencia.modulo.ciclo.año_academico

    @cached_property
    def profesor(self):
        return self.docencia.profesor

    @cached_property
    def modulo(self):
        return self.docencia.modulo

    @cached_property
    def grupo(self):
        return self.docencia.grupo

    def __str__(self):
        return f"Seguimiento {self.docencia} - Mes {self.mes}"

    class Meta:
        # Garantizar un seguimiento al mes por docencia
        constraints = [
            models.UniqueConstraint(
                fields=["docencia", "mes"], name="docencia_mes_unicos"
            )
        ]
        indexes = [
            models.Index(fields=["mes"]),
            models.Index(fields=["docencia", "mes"]),
        ]


class RecordatorioEmailConfig(SingletonModel):
    """
    Configuración para los emails de recordatorio de seguimiento.
    Este modelo permite personalizar la plantilla de correo desde el admin.
    """

    asunto = models.CharField(
        max_length=255, default="Recordatorio de seguimiento pendiente - {{ mes }}"
    )

    contenido = models.TextField(
        default="""Estimado/a {{ nombre_profesor }},

Le recordamos que tiene pendiente realizar el seguimiento del mes de {{ mes }} para las siguientes docencias:

{{ listado_docencias }}

Puede completar los seguimientos pendientes haciendo clic en el siguiente enlace:
{{ url_frontend }}

Gracias por su colaboración.

Este es un correo automático, por favor no responda a esta dirección."""
    )

    help_text = models.TextField(
        verbose_name="Información de ayuda",
        default="""Variables disponibles:
- {{ nombre_profesor }}: Nombre del profesor
- {{ mes }}: Nombre del mes del seguimiento
- {{ listado_docencias }}: Lista de docencias pendientes
- {{ url_frontend }}: URL del frontend para acceder al sistema
Debes añadir por lo menos el mes y el listado de docencias al contenido.
Puedes poner las variables también en el asunto.
¡Cuidado, tienes que añadir un espacio antes y despues del nombre de cada variable! 
        """,
        editable=False,
    )

    def clean(self):
        """Verifica que la plantilla contenga las variables requeridas."""
        required_vars = [
            "{{ mes }}",
            "{{ listado_docencias }}",
        ]

        missing_vars = []
        for var in required_vars:
            if var not in self.contenido:
                missing_vars.append(var)

        if missing_vars:
            raise ValidationError(
                f"La plantilla debe contener las siguientes variables: {', '.join(missing_vars)}"
            )

    class Meta:
        verbose_name = "Configuración de Email de Recordatorio"
