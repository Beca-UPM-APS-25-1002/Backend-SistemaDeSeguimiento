from django.shortcuts import render
from .models import Seguimiento
from rest_framework import viewsets
from .serializers import SeguimientoSerializer
# Create your views here.


class SeguimientoViewSet(viewsets.ModelViewSet):
    queryset = Seguimiento.objects.all()
    serializer_class = SeguimientoSerializer
