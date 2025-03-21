from rest_framework import serializers
from .models import Seguimiento, Profesor


class ProfesorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profesor
        fields = ["nombre", "email"]


class SeguimientoSerializer(serializers.ModelSerializer):
    profesor = ProfesorSerializer()
    año_academico = serializers.ReadOnlyField()

    class Meta:
        model = Seguimiento
        fields = "__all__"
