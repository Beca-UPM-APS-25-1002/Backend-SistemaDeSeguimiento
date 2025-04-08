from rest_framework import serializers
from .models import (
    Seguimiento,
    Profesor,
    Modulo,
    Docencia,
    UnidadDeTrabajo,
    Grupo,
    AñoAcademico,
    Ciclo,
)


class AñoAcademicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AñoAcademico
        fields = "año_academico"


class CicloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ciclo
        fields = "__all__"


class UnidadDeTrabajoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadDeTrabajo
        fields = "__all__"


class ModuloSerializer(serializers.ModelSerializer):
    ciclo = CicloSerializer()

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
        fields = ["id", "nombre", "email", "activo", "is_admin"]


class DocenciaSerializer(serializers.ModelSerializer):
    profesor = ProfesorSerializer()
    modulo = ModuloSerializer()
    grupo = GrupoSerializer()

    class Meta:
        model = Docencia
        fields = "__all__"


class SeguimientoSerializer(serializers.ModelSerializer):
    profesor = ProfesorSerializer(required=False)

    class Meta:
        model = Seguimiento
        fields = "__all__"
        read_only_fields = ["profesor"]

    def validate(self, data):
        # Comprobar que el temario sea del modulo de la docencia

        docencia = data["docencia"]
        temario_actual = data["temario_actual"]
        mes = data["mes"]
        if temario_actual and docencia and temario_actual.modulo != docencia.modulo:
            raise serializers.ValidationError(
                {
                    "temario_actual": "El temario alcanzado debe pertenecer al módulo de la docencia."
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
    docencias = serializers.ListField(
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

    def validate_docencia_ids(self, value):
        if not value:
            raise serializers.ValidationError(
                "Debe proporcionar al menos un ID de docencia"
            )
        return value
