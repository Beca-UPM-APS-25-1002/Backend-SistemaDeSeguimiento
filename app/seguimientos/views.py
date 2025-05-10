from .models import (
    Seguimiento,
    Modulo,
    UnidadDeTrabajo,
    Docencia,
    RecordatorioEmailConfig,
)
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
from django.template import Template, Context
import calendar
from .serializers import (
    SeguimientoSerializer,
    ModuloSerializer,
    UnidadDeTrabajoSerializer,
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
            seguimientos = seguimientos.filter(
                docencia__modulo__ciclo__año_academico=year
            )
        if mes:
            seguimientos = seguimientos.filter(mes=mes)
        return seguimientos


class ModuloViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Modulo.objects.all()
    serializer_class = ModuloSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get"])
    def temario(self, request, pk):
        unidadesDeTemario = UnidadDeTrabajo.objects.filter(modulo=pk)
        if not unidadesDeTemario:
            return Response(
                "No existen unidades de temario para este modulo",
                status.HTTP_404_NOT_FOUND,
            )
        serializer = UnidadDeTrabajoSerializer(unidadesDeTemario, many=True)
        return Response(serializer.data)


class DocenciaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DocenciaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Docencia.objects.filter(
            profesor=self.request.user,
            modulo__ciclo__año_academico=get_año_academico_actual(),
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
        docencias = Docencia.objects.filter(modulo__ciclo__año_academico=año_academico)

        # Paso 2: Obtener todos los Seguimiento para el mes y año académico dados
        seguimientos = Seguimiento.objects.filter(
            mes=mes, docencia__modulo__ciclo__año_academico=año_academico
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


class SeguimientosFaltantesAnualView(generics.ListAPIView):
    """
    Vista que devuelve la lista de docencias sin seguimientos para un año académico completo,
    organizadas por mes. El resultado es un diccionario donde las claves son los nombres de
    los meses y los valores son listas de IDs de docencias sin seguimientos.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        año_academico = self.kwargs["año_academico"]
        user = self.request.user

        # Diccionario para almacenar los resultados por mes
        resultados_por_mes = {}

        # Paso 1: Filtrar las instancias de Docencia por año académico
        docencias = Docencia.objects.filter(modulo__ciclo__año_academico=año_academico)

        # Si no es administrador o no se solicitan todas, filtrar por profesor
        if not (user.is_admin and self.request.query_params.get("all") is not None):
            docencias = docencias.filter(profesor=user)

        # Iterar sobre cada mes
        for num_mes in range(1, 13):
            # Paso 2: Obtener todos los Seguimiento para el mes y año académico dados
            seguimientos = Seguimiento.objects.filter(
                mes=num_mes, docencia__modulo__ciclo__año_academico=año_academico
            )

            # Paso 3: Excluir las Docencia que ya tienen un Seguimiento para el mes dado
            docencias_con_seguimiento = seguimientos.values_list("docencia", flat=True)
            docencias_sin_seguimiento = docencias.exclude(
                id__in=docencias_con_seguimiento
            )

            # Paso 4: Excluir las Docencia donde otra Docencia con el mismo grupo y módulo ya tiene un Seguimiento
            for seguimiento in seguimientos:
                docencias_sin_seguimiento = docencias_sin_seguimiento.exclude(
                    grupo=seguimiento.docencia.grupo, modulo=seguimiento.docencia.modulo
                )

            # Añadir los IDs de docencias sin seguimiento al resultado para este mes
            if docencias_sin_seguimiento.exists():
                resultados_por_mes[num_mes] = list(
                    docencias_sin_seguimiento.values_list("id", flat=True)
                )
        return Response(resultados_por_mes)


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
    - docencias: lista de IDs de docencias
    - mes: mes para el cual falta el seguimiento
    - año_academico: año académico del seguimiento
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = RecordatorioSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        docencias = serializer.validated_data["docencias"]
        mes = serializer.validated_data["mes"]
        mes_nombre = calendar.month_name[mes].capitalize()

        # Obtener la configuración del email
        email_config = RecordatorioEmailConfig.get_solo()

        # Diccionario para agrupar docencias por profesor
        profesores_docencias = {}
        docencias_no_encontradas = []
        profesores_no_activos = []

        # Recopilar todas las docencias agrupadas por profesor
        for docencia_id in docencias:
            try:
                docencia = Docencia.objects.get(id=docencia_id)

                if docencia.profesor.id not in profesores_docencias:
                    profesores_docencias[docencia.profesor.id] = {
                        "profesor": docencia.profesor,
                        "docencias": [],
                    }

                profesores_docencias[docencia.profesor.id]["docencias"].append(docencia)

            except Docencia.DoesNotExist:
                docencias_no_encontradas.append(docencia_id)

        # URL al frontend
        frontend_url = settings.FRONTEND_URL

        # Enviar emails personalizados a cada profesor
        emails_enviados = 0

        for profesor_data in profesores_docencias.values():
            profesor = profesor_data["profesor"]
            docencias_profesor = profesor_data["docencias"]

            if not profesor.activo or not profesor.is_active:
                profesores_no_activos.append(profesor)
                continue

            # Preparar el listado de docencias
            listado_docencias = ""
            for docencia in docencias_profesor:
                listado_docencias += f"- {docencia.modulo.nombre} para el grupo {docencia.grupo.nombre}\n"

            # Contexto para renderizar la plantilla
            context = Context(
                {
                    "nombre_profesor": profesor.nombre,
                    "mes": mes_nombre,
                    "listado_docencias": listado_docencias,
                    "url_frontend": frontend_url,
                }
            )

            # Renderizar la plantilla
            asunto_template = Template(email_config.asunto)
            asunto = asunto_template.render(context)
            template = Template(email_config.contenido)
            mensaje = template.render(context)

            try:
                send_mail(
                    subject=asunto,
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
                "profesores_no_activos": [
                    profesor.email for profesor in profesores_no_activos
                ],
                "docencias_no_encontradas": docencias_no_encontradas,
            },
            status=status.HTTP_200_OK,
        )
