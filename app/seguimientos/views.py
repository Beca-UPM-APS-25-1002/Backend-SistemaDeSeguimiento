from .models import Seguimiento, Modulo, UnidadDeTemario, Docencia
from rest_framework import status, viewsets, generics
from django.db.models import Q
from rest_framework.views import APIView
from .utils import get_año_academico_actual
from rest_framework.decorators import action
from rest_framework.response import Response
from .permissions import TieneDocenciaConMismoGrupoModulo
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.mail import send_mail
from django.conf import settings
from .serializers import RecordatorioSerializer
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
    permission_classes = [IsAuthenticated & (TieneDocenciaConMismoGrupoModulo)]

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
        year = (
            get_año_academico_actual()
            if not self.request.query_params.get("year")
            else self.request.query_params.get("year")
        )
        mes = self.request.query_params.get("mes")
        if year:
            seguimientos = seguimientos.filter(docencia__modulo__año_academico=year)
        if mes:
            seguimientos = seguimientos.filter(mes=mes)
        return seguimientos


class ModuloViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Modulo.objects.all()
    serializer_class = ModuloSerializer
    permission_classes = [IsAuthenticated]

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


class DocenciaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DocenciaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Docencia.objects.filter(
            profesor=self.request.user,
            modulo__año_academico=get_año_academico_actual(),
        )


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
        # Si es administrador y quiere todas se le muestran, si no solo las del profesor
        if user.is_admin and self.request.query_params.get("all") is not None:
            return docencias_sin_seguimiento
        return docencias_sin_seguimiento.filter(profesor=user)


class CurrentAcademicYearView(APIView):
    permission_classes = [IsAuthenticated]
    allowed_methods = ["GET"]

    def get(self, request):
        return Response(
            {"año_academico_actual": get_año_academico_actual()},
            status=status.HTTP_200_OK,
        )


class EnviarRecordatorioSeguimientoView(APIView):
    """
    Vista para enviar recordatorios de seguimiento a profesores.

    Recibe un JSON con:
    - docencia_ids: lista de IDs de docencias
    - mes: mes para el cual falta el seguimiento
    - año_academico: año académico del seguimiento
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = RecordatorioSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        docencia_ids = serializer.validated_data["docencia_ids"]
        mes = serializer.validated_data["mes"]
        año_academico = serializer.validated_data["año_academico"]

        # Diccionario para agrupar docencias por profesor
        profesores_docencias = {}
        docencias_no_encontradas = []
        profesores_no_activos = []
        # Recopilar todas las docencias agrupadas por profesor
        for docencia_id in docencia_ids:
            try:
                docencia = Docencia.objects.select_related(
                    "profesor", "modulo", "grupo"
                ).get(id=docencia_id, modulo__año_academico=año_academico)

                if docencia.profesor.id not in profesores_docencias:
                    profesores_docencias[docencia.profesor.id] = {
                        "profesor": docencia.profesor,
                        "docencias": [],
                    }

                profesores_docencias[docencia.profesor.id]["docencias"].append(docencia)

            except Docencia.DoesNotExist:
                docencias_no_encontradas.append(docencia_id)

        # Enviar emails personalizados a cada profesor
        emails_enviados = 0
        nombres_meses = {
            1: "enero",
            2: "febrero",
            3: "marzo",
            4: "abril",
            5: "mayo",
            6: "junio",
            7: "julio",
            8: "agosto",
            9: "septiembre",
            10: "octubre",
            11: "noviembre",
            12: "diciembre",
        }

        for profesor_data in profesores_docencias.values():
            profesor = profesor_data["profesor"]
            docencias = profesor_data["docencias"]

            if not profesor.activo or not profesor.is_active:
                profesores_no_activos.append(profesor)
                continue

            # Construir mensaje personalizado
            mensaje = f"""
            Estimado/a {profesor.nombre},
            
            Le recordamos que tiene pendiente realizar el seguimiento del mes de {nombres_meses[mes]} para las siguientes docencias:
            
            """

            for docencia in docencias:
                mensaje += (
                    f"- {docencia.modulo.nombre} del grupo {docencia.grupo.nombre}\n"
                )

            # URL al frontend (configurar en settings.py)
            frontend_url = f"{settings.FRONTEND_URL}"

            mensaje += f"""
            
            Puede completar los seguimientos pendientes haciendo clic en el siguiente enlace:
            {frontend_url}
            
            Gracias por su colaboración.
            
            Este es un correo automático, por favor no responda a esta dirección.
            """

            try:
                send_mail(
                    subject=f"Recordatorio de seguimiento pendiente - {nombres_meses[mes]} {año_academico}",
                    message=mensaje,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[profesor.email],
                    fail_silently=False,
                )
                emails_enviados += 1
            except Exception:
                continue
        return Response(
            {
                "status": "success",
                "detail": f"Se enviaron {emails_enviados} recordatorios de seguimiento",
                "emails_enviados": emails_enviados,
                "total_profesores": len(profesores_docencias),
                "profesores_no_activos": profesores_no_activos,
                "docencias_no_encontradas": docencias_no_encontradas,
            },
            status=status.HTTP_200_OK,
        )
