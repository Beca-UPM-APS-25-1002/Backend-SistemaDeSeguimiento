# permisos.py
from rest_framework import permissions
from .models import Docencia


class TieneDocenciaConMismoGrupoModulo(permissions.BasePermission):
    """
    Permiso personalizado que permite a los profesores acceder únicamente a los seguimientos
    donde tienen una docencia con el mismo grupo y módulo.
    """

    def has_permission(self, request, view):
        """
        Comprobación de permisos para operaciones de listado.
        Para operaciones de creación, verifica que el profesor tenga una docencia
        con el mismo grupo y módulo.
        """
        # Siempre requiere autenticación
        if not request.user.is_authenticated:
            return False

        # Para operaciones de creación, comprueba si el usuario tiene una docencia
        # con el mismo grupo y módulo
        if request.method == "POST":
            docencia_id = request.data.get("docencia")
            if not docencia_id:
                return False

            try:
                # Obtiene la docencia para la que se está creando el seguimiento
                docencia_objetivo = Docencia.objects.get(id=docencia_id)

                # Comprueba si el profesor tiene alguna docencia con el mismo grupo y módulo
                return Docencia.objects.filter(
                    profesor=request.user,
                    grupo=docencia_objetivo.grupo,
                    modulo=docencia_objetivo.modulo,
                ).exists()
            except Docencia.DoesNotExist:
                return False

        # Para operaciones de listado, permite el acceso (se filtrará en get_queryset)
        return True

    def has_object_permission(self, request, view, obj):
        """
        Comprobación de permisos a nivel de objeto.
        Asegura que el profesor tenga una docencia con el mismo grupo y módulo
        que la docencia del seguimiento.
        """
        # Obtiene el grupo y módulo de la docencia del seguimiento
        grupo = obj.docencia.grupo
        modulo = obj.docencia.modulo

        # Comprueba si el profesor tiene una docencia con el mismo grupo y módulo
        return Docencia.objects.filter(
            profesor=request.user, grupo=grupo, modulo=modulo
        ).exists()
