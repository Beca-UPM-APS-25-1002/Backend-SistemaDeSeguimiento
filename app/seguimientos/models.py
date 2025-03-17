from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.functional import cached_property


class Ciclo(models.Model):
    nombre = models.CharField(null=False, max_length=255, primary_key=True)


class Grupo(models.Model):
    nombre = models.CharField(null=False, max_length=255, primary_key=True)
    ciclo = models.ForeignKey(
        Ciclo, on_delete=models.RESTRICT, to_field="nombre", related_name="grupos"
    )


class Modulo(models.Model):
    nombre = models.CharField(null=False, max_length=255)
    curso = models.IntegerField(null=False)
    año_academico = models.CharField(null=False, max_length=10, db_index=True)
    ciclo = models.ForeignKey(
        Ciclo, on_delete=models.RESTRICT, to_field="nombre", related_name="modulos"
    )

    class Meta:
        indexes = [
            models.Index(fields=["año_academico"]),
            models.Index(fields=["ciclo"]),
        ]


class UnidadDeTemario(models.Model):
    numero_tema = models.IntegerField(null=False)
    titulo = models.CharField(max_length=255, null=False)
    impartido = models.BooleanField(default=False)
    modulo = models.ForeignKey(
        Modulo, on_delete=models.CASCADE, related_name="unidades_de_temario"
    )

    @property
    def año_academico(self):
        return self.modulo.año_academico


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

    USERNAME_FIELD = "email"  # Use email as the unique identifier
    REQUIRED_FIELDS = ["nombre"]  # Required fields for createsuperuser

    def __str__(self):
        return self.nombre


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
        return self.modulo.año_academico

    class Meta:
        # Ensure a professor isn't assigned to the same module and group twice in the same academic year
        unique_together = ["profesor", "grupo", "modulo"]
        indexes = [
            models.Index(fields=["profesor", "modulo"]),
            models.Index(fields=["grupo", "modulo"]),
        ]

    def __str__(self):
        return f"{self.profesor.nombre} - {self.modulo.nombre} - {self.grupo.nombre}"


class EstadoSeguimiento(models.TextChoices):
    ATRASADO = "ATRASADO", "Atrasado"
    AL_DIA = "AL_DIA", "Al día"
    ADELANTADO = "ADELANTADO", "Adelantado"


class Seguimiento(models.Model):
    temario_alcanzado = models.ForeignKey(
        UnidadDeTemario, on_delete=models.RESTRICT, related_name="seguimientos"
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
    mes = models.IntegerField()
    docencia = models.ForeignKey(
        Docencia, on_delete=models.CASCADE, related_name="seguimientos"
    )

    @cached_property
    def año_academico(self):
        return self.docencia.modulo.año_academico

    @cached_property
    def profesor(self):
        return self.docencia.profesor

    def __str__(self):
        return f"Seguimiento {self.docencia} - Mes {self.mes}"

    class Meta:
        # Ensure one tracking per month per teaching assignment
        unique_together = ["docencia", "mes"]
        indexes = [
            models.Index(fields=["mes"]),
            models.Index(fields=["docencia", "mes"]),
        ]
