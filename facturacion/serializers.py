"""Transformación y validación de entradas de la API."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import (
    Cliente,
    Comprobante,
    DetalleComprobante,
    Empresa,
    HistorialEstado,
    LogEnvioSUNAT,
    Membresia,
    NotaCredito,
    Producto,
    SerieComprobante,
)


class ValidacionModeloMixin:
    """Ejecuta las validaciones de dominio también para escrituras REST."""

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = self.instance or self.Meta.model()
        for campo, valor in attrs.items():
            setattr(instance, campo, valor)
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return attrs


class EmpresaSerializer(ValidacionModeloMixin, serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = "__all__"


class SerieComprobanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SerieComprobante
        fields = "__all__"
        read_only_fields = ["empresa", "correlativo_actual"]
        validators = []

    def validate_serie(self, value):
        if len(value) != 4 or not value.isascii() or not value.isalnum():
            raise serializers.ValidationError(
                "La serie debe tener cuatro caracteres alfanuméricos."
            )
        return value.upper()


class ClienteSerializer(ValidacionModeloMixin, serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"
        read_only_fields = ["empresa"]
        validators = []


class ProductoSerializer(ValidacionModeloMixin, serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = "__all__"
        read_only_fields = ["empresa"]
        validators = []


class DetalleComprobanteSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="descripcion_historica", read_only=True)

    class Meta:
        model = DetalleComprobante
        fields = [
            "id",
            "producto",
            "producto_nombre",
            "cantidad",
            "precio_unitario",
            "descuento",
            "igv_linea",
            "subtotal",
        ]


class ComprobanteSerializer(serializers.ModelSerializer):
    detalles = DetalleComprobanteSerializer(many=True, read_only=True)
    cliente_nombre = serializers.SerializerMethodField()
    cliente_num_doc = serializers.SerializerMethodField()
    saldo_disponible = serializers.SerializerMethodField()

    class Meta:
        model = Comprobante
        fields = [
            "id",
            "empresa",
            "serie",
            "numero",
            "fecha",
            "cliente",
            "cliente_nombre",
            "cliente_num_doc",
            "tipo",
            "subtotal",
            "igv",
            "total",
            "estado",
            "detalles",
            "saldo_disponible",
        ]

    def get_cliente_nombre(self, obj) -> str:
        return obj.datos_historicos.get("cliente", {}).get("razon_social", obj.cliente.razon_social)

    def get_cliente_num_doc(self, obj) -> str:
        return obj.datos_historicos.get("cliente", {}).get("num_doc", obj.cliente.num_doc)

    def get_saldo_disponible(self, obj) -> Decimal:
        from .services import saldo_credito

        return saldo_credito(obj) if obj.tipo in {"01", "03"} else Decimal("0")


class ItemInputSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField(min_value=1)
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    precio_unitario = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False
    )
    descuento = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, default=Decimal("0")
    )


class EmitirComprobanteInputSerializer(serializers.Serializer):
    empresa_id = serializers.IntegerField(required=False)
    cliente_id = serializers.IntegerField(min_value=1)
    items = ItemInputSerializer(many=True, allow_empty=False)
    borrador = serializers.BooleanField(default=False)
    serie = serializers.CharField(max_length=4, required=False)
    resultado_mock = serializers.ChoiceField(choices=["ACEPTADO", "RECHAZADO"], default="ACEPTADO")
    clave_idempotencia = serializers.CharField(max_length=100, required=False)


class NotaCreditoInputSerializer(serializers.Serializer):
    comprobante_id = serializers.IntegerField(min_value=1)
    motivo = serializers.CharField(max_length=1000)
    tipo_nota = serializers.ChoiceField(choices=["01", "02", "03", "06", "07"])
    monto_afectado = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    clave_idempotencia = serializers.CharField(max_length=100, required=False)
    resultado_mock = serializers.ChoiceField(choices=["ACEPTADO", "RECHAZADO"], default="ACEPTADO")


class ReenvioInputSerializer(serializers.Serializer):
    """Selecciona únicamente el resultado del procesamiento simulado."""

    resultado_mock = serializers.ChoiceField(choices=["ACEPTADO", "RECHAZADO"], default="ACEPTADO")


class FilaVentaSerializer(serializers.Serializer):
    """Describe una fila contable con signo negativo para créditos."""

    id = serializers.IntegerField()
    fecha = serializers.DateField()
    tipo = serializers.CharField()
    documento = serializers.CharField()
    cliente = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2)
    igv = serializers.DecimalField(max_digits=14, decimal_places=2)
    total = serializers.DecimalField(max_digits=14, decimal_places=2)


class ResumenVentasSerializer(serializers.Serializer):
    total_subtotal = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_igv = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_ventas = serializers.DecimalField(max_digits=18, decimal_places=2)
    notas_credito = serializers.DecimalField(max_digits=18, decimal_places=2)
    cantidad_comprobantes = serializers.IntegerField()
    rechazados = serializers.IntegerField()


class LibroVentasSerializer(serializers.Serializer):
    mes = serializers.IntegerField()
    anio = serializers.IntegerField()
    resumen = ResumenVentasSerializer()
    comprobantes = FilaVentaSerializer(many=True)


class ConteoEstadoSerializer(serializers.Serializer):
    estado = serializers.CharField()
    cantidad = serializers.IntegerField()


class ConteoTipoSerializer(serializers.Serializer):
    tipo = serializers.CharField()
    cantidad = serializers.IntegerField()


class DashboardSerializer(LibroVentasSerializer):
    estados = ConteoEstadoSerializer(many=True)
    tipos = ConteoTipoSerializer(many=True)


class NotaCreditoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaCredito
        fields = "__all__"


class LogEnvioSUNATSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEnvioSUNAT
        fields = "__all__"


class HistorialEstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialEstado
        fields = "__all__"


class MembresiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membresia
        fields = "__all__"
        read_only_fields = ["empresa"]
        validators = []


class UsuarioSerializer(serializers.ModelSerializer):
    """Crea cuentas locales sin conceder privilegios globales de Django."""

    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)
    rol = serializers.ChoiceField(choices=Membresia.ROLES, write_only=True, required=False)
    rol_empresa = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "rol",
            "rol_empresa",
        ]

    def get_rol_empresa(self, obj) -> str:
        return obj.membresias.get(empresa=self.context["request"].empresa).rol

    def validate(self, attrs):
        if not self.instance and ("password" not in attrs or "rol" not in attrs):
            raise serializers.ValidationError("Indique contraseña y rol para la nueva cuenta.")
        if "password" in attrs:
            candidato = self.instance or get_user_model()(username=attrs.get("username", ""))
            try:
                validate_password(attrs["password"], candidato)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"password": exc.messages}) from exc
        return attrs

    def create(self, validated_data):
        from django.db import transaction

        with transaction.atomic():
            rol = validated_data.pop("rol")
            usuario = get_user_model().objects.create_user(**validated_data)
            Membresia.objects.create(
                usuario=usuario, empresa=self.context["request"].empresa, rol=rol
            )
        return usuario

    def update(self, instance, validated_data):
        from django.db import transaction

        empresa = self.context["request"].empresa
        if instance.membresias.exclude(empresa=empresa).exists():
            raise serializers.ValidationError(
                "La cuenta es compartida con otra empresa. Gestione su membresía local o contacte al superusuario."
            )
        with transaction.atomic():
            rol = validated_data.pop("rol", None)
            password = validated_data.pop("password", None)
            if password:
                instance.set_password(password)
            instance = super().update(instance, validated_data)
            if rol:
                Membresia.objects.filter(usuario=instance, empresa=empresa).update(rol=rol)
        return instance
