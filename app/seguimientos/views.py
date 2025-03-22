from .models import Seguimiento, Modulo, UnidadDeTemario, Docencia
from rest_framework import status, viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import (
    SeguimientoSerializer,
    ModuloSerializer,
    UnidadDeTemarioSerializer,
    DocenciaSerializer,
)


class SeguimientoViewSet(viewsets.ModelViewSet):
    queryset = Seguimiento.objects.all()
    serializer_class = SeguimientoSerializer


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

    serializer_class = DocenciaSerializer

    def get_queryset(self):
        año_academico = self.kwargs["año_academico"]
        mes = self.kwargs["mes"]

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

        return docencias_sin_seguimiento
