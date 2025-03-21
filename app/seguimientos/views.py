from django.shortcuts import render
from .models import Seguimiento, Modulo, UnidadDeTemario
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import (
    SeguimientoSerializer,
    ModuloSerializer,
    UnidadDeTemarioSerializer,
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
