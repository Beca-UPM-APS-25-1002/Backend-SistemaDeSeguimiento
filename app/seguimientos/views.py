from .models import Seguimiento, Modulo, UnidadDeTemario, Docencia
from rest_framework import status, viewsets, generics
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response
from .permissions import TieneDocenciaConMismoGrupoModulo
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import (
    SeguimientoSerializer,
    ModuloSerializer,
    UnidadDeTemarioSerializer,
    DocenciaSerializer,
)


class SeguimientoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo Seguimiento.
    Restringe el acceso a seguimientos donde el profesor autenticado tiene
    una docencia con el mismo grupo y módulo.
    """

    serializer_class = SeguimientoSerializer
    permission_classes = [IsAuthenticated & TieneDocenciaConMismoGrupoModulo]

    def get_queryset(self):
        """
        Filtra el queryset para incluir solo los seguimientos donde el profesor
        tiene una docencia con el mismo grupo y módulo.
        """

        if not self.request.user.is_authenticated:
            return Seguimiento.objects.none()
        # Obtiene todas las docencias del profesor actual
        docencias_profesor = Docencia.objects.filter(profesor=self.request.user)

        # Crea un objeto Q para construir una consulta OR para cada par (grupo, módulo)
        consulta = Q()
        for docencia in docencias_profesor:
            # Añade condición para este par específico (grupo, módulo)
            consulta |= Q(
                docencia__grupo=docencia.grupo, docencia__modulo=docencia.modulo
            )

        # Si el profesor no tiene docencias, devuelve un queryset vacío
        if not docencias_profesor.exists():
            return Seguimiento.objects.none()

        # Devuelve los seguimientos que coinciden con cualquiera de los pares (grupo, módulo) del profesor
        seguimientos = Seguimiento.objects.filter(consulta)

        # Filtra los seguimientos por parametros pasados en la URL
        year = self.request.query_params.get("year")
        mes = self.request.query_params.get("mes")
        if year:
            seguimientos = seguimientos.filter(docencia__modulo__año_academico=year)
        if mes:
            seguimientos = seguimientos.filter(mes=mes)
        return seguimientos


class ModuloViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Modulo.objects.all()
    serializer_class = ModuloSerializer

    @action(detail=True, methods=["get"])
    def temario(self, request, pk):
        unidadesDeTemario = UnidadDeTemario.objects.filter(modulo=pk)
        if not unidadesDeTemario:
            return Response(
                "No existen unidades de temario para este modulo",
                status.HTTP_404_NOT_FOUND,
            )
        serializer = UnidadDeTemarioSerializer(unidadesDeTemario, many=True)
        return Response(serializer.data)


class SeguimientosFaltantesView(generics.ListAPIView):
    """
    Vista que devuelve la lista de docencias que
    no han realizado un seguimiento para un año academico y mes concretos.
    Evalua seguimientos por mes, grupo y modulo, lo que significa
    que si un profesor ya ha realizado el seguimiento del mes para
    un grupo y modulo, se considera que todas las docencias asociadas
    han completado el seguimiento.
    """

    permission_classes = [IsAuthenticated]

    serializer_class = DocenciaSerializer

    def get_queryset(self):
        año_academico = self.kwargs["año_academico"]
        mes = self.kwargs["mes"]
        user = self.request.user
        # Paso 1: Filtrar las instancias de Docencia por año académico
        docencias = Docencia.objects.filter(modulo__año_academico=año_academico)

        # Paso 2: Obtener todos los Seguimiento para el mes y año académico dados
        seguimientos = Seguimiento.objects.filter(
            mes=mes, docencia__modulo__año_academico=año_academico
        )

        # Paso 3: Excluir las Docencia que ya tienen un Seguimiento para el mes dado
        docencias_con_seguimiento = seguimientos.values_list("docencia", flat=True)
        docencias_sin_seguimiento = docencias.exclude(id__in=docencias_con_seguimiento)

        # Paso 4: Excluir las Docencia donde otra Docencia con el mismo grupo y módulo ya tiene un Seguimiento
        for seguimiento in seguimientos:
            docencias_sin_seguimiento = docencias_sin_seguimiento.exclude(
                grupo=seguimiento.docencia.grupo, modulo=seguimiento.docencia.modulo
            )
        if user.is_admin:
            return docencias_sin_seguimiento
        return docencias_sin_seguimiento.filter(profesor=user)
