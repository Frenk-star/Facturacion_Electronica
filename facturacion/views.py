"""Endpoints REST: transporte HTTP, filtros y delegación a servicios."""

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Cliente,
    Comprobante,
    Empresa,
    Membresia,
    NotaCredito,
    Producto,
    SerieComprobante,
)
from .pdf_utils import generar_pdf
from .permissions import PermisoEmpresa
from .reportes import PeriodoSerializer, exportar_libro, libro_ventas
from .serializers import (
    ClienteSerializer,
    ComprobanteSerializer,
    DashboardSerializer,
    EmitirComprobanteInputSerializer,
    EmpresaSerializer,
    HistorialEstadoSerializer,
    LibroVentasSerializer,
    LogEnvioSUNATSerializer,
    MembresiaSerializer,
    NotaCreditoInputSerializer,
    NotaCreditoSerializer,
    ProductoSerializer,
    ReenvioInputSerializer,
    SerieComprobanteSerializer,
    UsuarioSerializer,
)
from .services import FacturacionService


class FiltrosComprobanteSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=["01", "03", "07"], required=False)
    estado = serializers.ChoiceField(
        choices=[item[0] for item in Comprobante.ESTADO_CHOICES], required=False
    )
    fecha_desde = serializers.DateField(required=False)
    fecha_hasta = serializers.DateField(required=False)
    ruc_cliente = serializers.CharField(required=False)
    cliente = serializers.IntegerField(min_value=1, required=False)

    def validate(self, attrs):
        if (
            attrs.get("fecha_desde")
            and attrs.get("fecha_hasta")
            and attrs["fecha_desde"] > attrs["fecha_hasta"]
        ):
            raise serializers.ValidationError("La fecha inicial no puede superar la final.")
        return attrs


def filtrar_comprobantes(queryset, parametros):
    """Valida fechas y filtros antes de construir consultas SQL."""
    filtros = FiltrosComprobanteSerializer(data=parametros)
    filtros.is_valid(raise_exception=True)
    campos = {
        "tipo": "tipo",
        "estado": "estado",
        "fecha_desde": "fecha__date__gte",
        "fecha_hasta": "fecha__date__lte",
        "ruc_cliente": "cliente__num_doc",
        "cliente": "cliente_id",
    }
    for clave, valor in filtros.validated_data.items():
        queryset = queryset.filter(**{campos[clave]: valor})
    return queryset


class AmbitoMixin:
    permission_classes = [PermisoEmpresa]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        return super().get_queryset().filter(empresa=self.request.empresa)


class CatalogoViewSet(AmbitoMixin, viewsets.ModelViewSet):
    """Mantenimiento aislado con desactivación en lugar de borrado físico."""

    def get_queryset(self):
        queryset = super().get_queryset().order_by("pk")
        termino = self.request.query_params.get("q", "")
        if termino:
            campos = (
                ["num_doc", "razon_social"]
                if self.queryset.model == Cliente
                else ["codigo", "descripcion"]
            )
            queryset = queryset.filter(
                Q(**{f"{campos[0]}__icontains": termino})
                | Q(**{f"{campos[1]}__icontains": termino})
            )
        if self.request.query_params.get("activo") == "true":
            queryset = queryset.filter(activo=True)
        return queryset

    def _guardar(self, serializer):
        try:
            with transaction.atomic():
                objeto = serializer.save(empresa=self.request.empresa)
                objeto.full_clean()
        except IntegrityError as exc:
            raise serializers.ValidationError(
                "Ya existe un registro con ese código o documento en su empresa."
            ) from exc

    def perform_create(self, serializer):
        self._guardar(serializer)

    def perform_update(self, serializer):
        self._guardar(serializer)

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save(update_fields=["activo"])


class ClienteViewSet(CatalogoViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    @action(detail=True, methods=["get"])
    def historial(self, request, pk=None):
        documentos = (
            self.get_object().comprobantes.filter(empresa=request.empresa).order_by("-fecha")
        )
        pagina = self.paginate_queryset(documentos)
        return self.get_paginated_response(ComprobanteSerializer(pagina, many=True).data)


class ProductoViewSet(CatalogoViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer


class EmpresaViewSet(viewsets.ModelViewSet):
    """Edita la empresa activa; crear/eliminar empresas exige superusuario."""

    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [PermisoEmpresa]
    solo_admin = True
    http_method_names = ["get", "patch", "put", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        return Empresa.objects.filter(pk=self.request.empresa.pk)


class SerieComprobanteViewSet(AmbitoMixin, viewsets.ModelViewSet):
    queryset = SerieComprobante.objects.all()
    serializer_class = SerieComprobanteSerializer
    solo_admin = True
    http_method_names = ["get", "post", "head", "options"]

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(empresa=self.request.empresa)
        except IntegrityError as exc:
            raise serializers.ValidationError("La serie ya existe.") from exc


class MembresiaViewSet(AmbitoMixin, viewsets.ModelViewSet):
    """Gestiona roles dentro de la empresa activa sin permisos globales."""

    queryset = Membresia.objects.select_related("usuario")
    serializer_class = MembresiaSerializer
    solo_admin = True

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(empresa=self.request.empresa)
        except IntegrityError as exc:
            raise serializers.ValidationError("La membresía ya existe en esta empresa.") from exc

    def perform_update(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(empresa=self.request.empresa)
        except IntegrityError as exc:
            raise serializers.ValidationError("La membresía ya existe en esta empresa.") from exc


class UsuarioViewSet(viewsets.ModelViewSet):
    """Administra cuentas del ámbito local; desactivar revoca la membresía local."""

    queryset = get_user_model().objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [PermisoEmpresa]
    solo_admin = True

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        if (
            not self.request.user.is_superuser
            and not self.request.empresa.membresias.filter(
                usuario=self.request.user, rol="ADMIN", activo=True
            ).exists()
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Solo administradores pueden consultar usuarios.")
        return self.queryset.filter(membresias__empresa=self.request.empresa).order_by("pk")

    def perform_destroy(self, instance):
        Membresia.objects.filter(usuario=instance, empresa=self.request.empresa).update(
            activo=False
        )


@extend_schema(
    parameters=[
        OpenApiParameter(name, type=str)
        for name in ["tipo", "estado", "fecha_desde", "fecha_hasta", "ruc_cliente", "cliente"]
    ]
)
class ComprobanteViewSet(AmbitoMixin, viewsets.ReadOnlyModelViewSet):
    """Expone documentos inmutables y acciones explícitas de negocio."""

    queryset = (
        Comprobante.objects.select_related("empresa", "cliente")
        .prefetch_related("detalles", "notas_credito")
        .order_by("-fecha", "-pk")
    )
    serializer_class = ComprobanteSerializer

    def get_queryset(self):
        return filtrar_comprobantes(super().get_queryset(), self.request.query_params)

    @extend_schema(request=EmitirComprobanteInputSerializer, responses={201: ComprobanteSerializer})
    @action(detail=False, methods=["post"], url_path="emitir-factura")
    def emitir_factura(self, request):
        return self._emitir(request, "01")

    @extend_schema(request=EmitirComprobanteInputSerializer, responses={201: ComprobanteSerializer})
    @action(detail=False, methods=["post"], url_path="emitir-boleta")
    def emitir_boleta(self, request):
        return self._emitir(request, "03")

    def _emitir(self, request, tipo_comp):
        entrada = EmitirComprobanteInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = dict(entrada.validated_data)
        empresa_id = datos.pop("empresa_id", request.empresa.pk)
        if empresa_id != request.empresa.pk:
            raise serializers.ValidationError("empresa_id no coincide con la empresa autorizada.")
        datos["items_data"] = datos.pop("items")
        documento = FacturacionService.emitir_comprobante(
            tipo_comp, request.empresa.pk, usuario=request.user, **datos
        )
        return Response(ComprobanteSerializer(documento).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses=ComprobanteSerializer)
    @action(detail=True, methods=["post"])
    def emitir(self, request, pk=None):
        documento = FacturacionService.emitir_borrador(self.get_object(), request.user)
        return Response(ComprobanteSerializer(documento).data)

    @extend_schema(request=ReenvioInputSerializer, responses=ComprobanteSerializer)
    @action(detail=True, methods=["post"], url_path="reenviar")
    def reenviar(self, request, pk=None):
        documento = self.get_object()
        if documento.estado != "RECHAZADO":
            raise serializers.ValidationError("Solo se pueden reenviar rechazados.")
        entrada = ReenvioInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        resultado = entrada.validated_data["resultado_mock"]
        FacturacionService.enviar_a_sunat(documento, resultado, request.user)
        return Response(ComprobanteSerializer(documento).data)

    @extend_schema(responses={(200, "application/pdf"): bytes})
    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        documento = self.get_object()
        response = HttpResponse(generar_pdf(documento), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="comprobante-{documento.pk}.pdf"'
        return response

    @extend_schema(responses={(200, "application/xml"): str})
    @action(detail=True, methods=["get"])
    def xml(self, request, pk=None):
        documento = self.get_object()
        if not documento.xml_firmado:
            raise serializers.ValidationError("El borrador aún no tiene XML.")
        response = HttpResponse(
            documento.xml_firmado, content_type="application/xml; charset=utf-8"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{documento.serie}-{documento.numero}.xml"'
        )
        return response

    @extend_schema(responses=LogEnvioSUNATSerializer(many=True))
    @action(detail=True, methods=["get"])
    def logs(self, request, pk=None):
        return Response(
            LogEnvioSUNATSerializer(
                self.get_object().logs_sunat.order_by("fecha_envio"), many=True
            ).data
        )

    @extend_schema(responses=HistorialEstadoSerializer(many=True))
    @action(detail=True, methods=["get"])
    def historial(self, request, pk=None):
        return Response(
            HistorialEstadoSerializer(self.get_object().historial.order_by("fecha"), many=True).data
        )


class NotaCreditoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NotaCredito.objects.select_related("comprobante", "comprobante_referencia")
    serializer_class = NotaCreditoSerializer
    permission_classes = [PermisoEmpresa]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        return self.queryset.filter(comprobante_referencia__empresa=self.request.empresa).order_by(
            "-pk"
        )

    @extend_schema(request=NotaCreditoInputSerializer, responses={201: NotaCreditoSerializer})
    def create(self, request, *args, **kwargs):
        entrada = NotaCreditoInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = dict(entrada.validated_data)
        original = get_object_or_404(
            Comprobante, pk=datos.pop("comprobante_id"), empresa=request.empresa
        )
        nota = FacturacionService.emitir_nota_credito(original.pk, usuario=request.user, **datos)
        return Response(NotaCreditoSerializer(nota).data, status=201)


class ReportesViewSet(viewsets.ViewSet):
    """Comparte el libro mensual entre JSON y exportaciones descargables."""

    permission_classes = [PermisoEmpresa]
    serializer_class = PeriodoSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("mes", int),
            OpenApiParameter("anio", int),
            OpenApiParameter("formato", str),
        ],
        responses=LibroVentasSerializer,
    )
    @action(detail=False, methods=["get"], url_path="ventas-por-periodo")
    def ventas_por_periodo(self, request):
        libro = libro_ventas(
            Comprobante.objects.filter(empresa=request.empresa), request.query_params
        )
        formato = request.query_params.get("formato")
        if formato in {"csv", "xlsx"}:
            return exportar_libro(libro, formato)
        if formato:
            raise serializers.ValidationError("Formato permitido: csv o xlsx.")
        return Response(libro)

    @extend_schema(responses=DashboardSerializer)
    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        hoy = timezone.localdate()
        documentos = Comprobante.objects.filter(
            empresa=request.empresa, fecha__month=hoy.month, fecha__year=hoy.year
        )
        return Response(
            {
                "estados": list(documentos.values("estado").annotate(cantidad=Count("id"))),
                "tipos": list(documentos.values("tipo").annotate(cantidad=Count("id"))),
                **libro_ventas(documentos, {}),
            }
        )
