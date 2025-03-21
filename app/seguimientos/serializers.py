from rest_framework import serializers
from .models import Seguimiento, Profesor, Modulo, UnidadDeTemario


class UnidadDeTemarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadDeTemario
        fields = "__all__"


class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modulo
        fields = "__all__"


class ProfesorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profesor
        fields = ["id", "nombre", "email"]


class SeguimientoSerializer(serializers.ModelSerializer):
    profesor = ProfesorSerializer(required=False)
    año_academico = serializers.ReadOnlyField()

    class Meta:
        model = Seguimiento
        fields = "__all__"
        read_only_fields = ["profesor"]
