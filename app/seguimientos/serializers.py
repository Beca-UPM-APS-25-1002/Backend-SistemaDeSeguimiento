from rest_framework import serializers
from .models import Seguimiento, Profesor, Modulo, Docencia, UnidadDeTemario, Grupo
import re


class UnidadDeTemarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadDeTemario
        fields = "__all__"


class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modulo
        fields = "__all__"


class GrupoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grupo
        fields = "__all__"


class ProfesorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profesor
        fields = ["id", "nombre", "email", "activo"]


class DocenciaSerializer(serializers.ModelSerializer):
    profesor = ProfesorSerializer()
    modulo = ModuloSerializer()
    grupo = GrupoSerializer()

    class Meta:
        model = Docencia
        fields = "__all__"


class SeguimientoSerializer(serializers.ModelSerializer):
    profesor = ProfesorSerializer(required=False)
    año_academico = serializers.ReadOnlyField()

    class Meta:
        model = Seguimiento
        fields = "__all__"
        read_only_fields = ["profesor"]

    def validate(self, data):
        # Comprobar que el temario sea del modulo de la docencia

        docencia = data["docencia"]
        temario_alcanzado = data["temario_alcanzado"]
        mes = data["mes"]
        if temario_alcanzado and docencia:
            if temario_alcanzado.modulo != docencia.modulo:
                raise serializers.ValidationError(
                    {
                        "temario_alcanzado": "El temario alcanzado debe pertenecer al módulo de la docencia."
                    }
                )
        if "request" not in self.context:
            return data
        request = self.context["request"]
        if request.method == "POST":
            # Comprobar que no existe un seguimiento para esa combinacion de mes - grupo - modulo
            if docencia and mes:
                existing_seguimiento = Seguimiento.objects.filter(
                    docencia__grupo=docencia.grupo,
                    docencia__modulo=docencia.modulo,
                    mes=mes,
                ).exists()

                if existing_seguimiento:
                    raise serializers.ValidationError(
                        {
                            "docencia": "Ya existe un seguimiento para este mes, grupo y módulo."
                        }
                    )
            return data
        elif request.method in ["PUT", "PATCH"]:
            seguimiento = self.instance
            if mes != seguimiento.mes or docencia != seguimiento.docencia:
                raise serializers.ValidationError(
                    {
                        "docencia": "No puedes cambiar el mes o docencia de un seguimiento."
                    }
                )
            return data


class RecordatorioSerializer(serializers.Serializer):
    docencia_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=True,
        help_text="Lista de IDs de docencias para las que se enviará el recordatorio",
    )
    mes = serializers.IntegerField(
        min_value=1,
        max_value=12,
        required=True,
        help_text="Mes para el que falta el seguimiento (1-12)",
    )
    año_academico = serializers.CharField(
        required=True, help_text="Año académico del seguimiento (ej: '2024-2025')"
    )

    def validate_año_academico(self, value):
        return bool(re.search(r"^\d{4}-\d{2}$", value))

    def validate_docencia_ids(self, value):
        if not value:
            raise serializers.ValidationError(
                "Debe proporcionar al menos un ID de docencia"
            )
        return value
