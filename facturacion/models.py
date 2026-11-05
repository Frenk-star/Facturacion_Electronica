"""Entidades persistentes, restricciones y datos históricos de facturación."""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Round


class Empresa(models.Model):
    """Identidad fiscal del emisor; el RUC identifica una única empresa."""

    ruc = models.CharField(
        max_length=11,
        unique=True,
        validators=[RegexValidator(r"^\d{11}$", "El RUC debe tener 11 dígitos.")],
    )
    razon_social = models.CharField(max_length=255)
    nombre_comercial = models.CharField(max_length=255, blank=True, null=True)
    direccion = models.TextField()
    regimen_tributario = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.ruc} - {self.razon_social}"


class SerieComprobante(models.Model):
    """Contador transaccional independiente por empresa, tipo y serie."""

    TIPO_CHOICES = [("F", "Factura"), ("B", "Boleta"), ("FC", "Nota de Crédito/Débito")]
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES)
    serie = models.CharField(max_length=4)
    correlativo_actual = models.PositiveIntegerField(default=0)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="series")

    class Meta:
        unique_together = ("tipo", "serie", "empresa")

    def __str__(self):
        return f"{self.serie} ({self.get_tipo_display()})"


class Cliente(models.Model):
    """Receptor perteneciente a una empresa, susceptible de desactivación."""

    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, null=True, blank=True, related_name="clientes"
    )
    activo = models.BooleanField(default=True)
    TIPO_DOC_CHOICES = [("RUC", "RUC"), ("DNI", "DNI"), ("CE", "Carné de Extranjería")]
    tipo_doc = models.CharField(max_length=3, choices=TIPO_DOC_CHOICES)
    num_doc = models.CharField(max_length=15)
    razon_social = models.CharField(max_length=255)
    direccion = models.TextField()
    email = models.EmailField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "tipo_doc", "num_doc"], name="cliente_documento_empresa"
            )
        ]

    def clean(self):
        """Valida longitudes documentales antes de aceptar clientes."""
        largo = {"RUC": 11, "DNI": 8}.get(self.tipo_doc)
        if largo and (
            not self.num_doc.isascii() or not self.num_doc.isdigit() or len(self.num_doc) != largo
        ):
            raise ValidationError({"num_doc": f"El documento debe contener {largo} dígitos."})
        if self.tipo_doc == "CE" and not (6 <= len(self.num_doc) <= 15 and self.num_doc.isalnum()):
            raise ValidationError({"num_doc": "Carné de extranjería inválido."})

    def __str__(self):
        return f"{self.num_doc} - {self.razon_social}"


class Producto(models.Model):
    """Catálogo empresarial con precios finales que incluyen IGV."""

    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, null=True, blank=True, related_name="productos"
    )
    activo = models.BooleanField(default=True)
    codigo = models.CharField(max_length=50)
    descripcion = models.TextField()
    unidad_medida = models.CharField(max_length=10)
    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    afecto_igv = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["empresa", "codigo"], name="producto_codigo_empresa"),
            models.CheckConstraint(
                condition=Q(precio_unitario__gte=0), name="producto_precio_positivo"
            ),
        ]

    def __str__(self):
        return f"[{self.codigo}] {self.descripcion}"


class Comprobante(models.Model):
    """Documento de venta o crédito; sus importes se congelan al emitir."""

    ESTADO_CHOICES = [
        ("BORRADOR", "Borrador"),
        ("EMITIDO", "Emitido"),
        ("ENVIADO", "Enviado"),
        ("ACEPTADO", "Aceptado"),
        ("RECHAZADO", "Rechazado"),
    ]
    TIPO_COMPROBANTE = [("01", "Factura"), ("03", "Boleta"), ("07", "Nota de crédito")]

    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, related_name="comprobantes", null=True, blank=True
    )
    serie = models.CharField(max_length=4)
    numero = models.PositiveIntegerField(null=True, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    datos_historicos = models.JSONField(default=dict, blank=True)
    clave_idempotencia = models.CharField(max_length=100, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="comprobantes")
    tipo = models.CharField(max_length=2, choices=TIPO_COMPROBANTE)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    igv = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default="BORRADOR")
    xml_firmado = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "tipo", "serie", "numero"], name="numero_documento_empresa"
            ),
            models.UniqueConstraint(
                fields=["empresa", "clave_idempotencia"], name="emision_idempotente_empresa"
            ),
            models.CheckConstraint(
                condition=Q(total__gte=0) & Q(subtotal__gte=0) & Q(igv__gte=0),
                name="importes_no_negativos",
            ),
            models.CheckConstraint(
                condition=Q(estado="BORRADOR", numero__isnull=True)
                | (~Q(estado="BORRADOR") & Q(numero__isnull=False) & Q(numero__gt=0)),
                name="numero_solo_emitidos",
            ),
            models.CheckConstraint(
                condition=Q(total=Round(models.F("subtotal") + models.F("igv"), 2)),
                name="total_suma_base_igv",
            ),
        ]
        indexes = [
            models.Index(fields=["empresa", "fecha", "estado"]),
            models.Index(fields=["empresa", "tipo"]),
        ]

    def clean(self):
        """Comprueba identidad del receptor y coherencia del ámbito empresarial."""
        super().clean()
        if self.cliente_id:
            if self.empresa_id and self.cliente.empresa_id != self.empresa_id:
                raise ValidationError("Cliente y comprobante deben pertenecer a la misma empresa.")
            if self.tipo == "01" and (
                self.cliente.tipo_doc != "RUC"
                or len(self.cliente.num_doc) != 11
                or not self.cliente.num_doc.isascii()
                or not self.cliente.num_doc.isdigit()
            ):
                raise ValidationError(
                    "Las facturas (tipo 01) solo pueden emitirse a clientes con RUC de 11 dígitos."
                )

    def __str__(self):
        numero = f"{self.numero:08d}" if self.numero else "BORRADOR"
        return f"{self.serie}-{numero} ({self.estado})"

    def delete(self, *args, **kwargs):
        """Conserva todo documento numerado y su evidencia tributaria."""
        if self.estado != "BORRADOR":
            raise ValidationError("Los documentos emitidos no se pueden eliminar.")
        return super().delete(*args, **kwargs)


class DetalleComprobante(models.Model):
    """Línea con cantidades, importes y descripción histórica del producto."""

    descripcion_historica = models.TextField(blank=True)
    unidad_historica = models.CharField(max_length=10, blank=True)
    afecto_igv_historico = models.BooleanField(default=True)
    comprobante = models.ForeignKey(Comprobante, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    igv_linea = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(cantidad__gt=0)
                & Q(precio_unitario__gte=0)
                & Q(descuento__gte=0)
                & Q(igv_linea__gte=0)
                & Q(subtotal__gte=0),
                name="detalle_importes_validos",
            )
        ]

    def clean(self):
        """Evita descuentos excesivos y relaciones entre catálogos de otra empresa."""
        if (
            self.cantidad is not None
            and self.precio_unitario is not None
            and self.descuento > self.cantidad * self.precio_unitario
        ):
            raise ValidationError("El descuento no puede superar el importe de la línea.")
        if (
            self.producto_id
            and self.comprobante_id
            and self.producto.empresa_id != self.comprobante.empresa_id
        ):
            raise ValidationError("El producto no pertenece a la empresa del comprobante.")

    def __str__(self):
        return f"{self.comprobante_id}: {self.descripcion_historica or self.producto_id}"


class LogEnvioSUNAT(models.Model):
    """Resultado inalterable de un intento de procesamiento OSE simulado."""

    comprobante = models.ForeignKey(
        Comprobante, on_delete=models.PROTECT, related_name="logs_sunat"
    )
    fecha_envio = models.DateTimeField(auto_now_add=True)
    estado_respuesta = models.CharField(max_length=20)
    codigo_respuesta = models.CharField(max_length=10)
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.comprobante_id}: {self.codigo_respuesta}"


class NotaCredito(models.Model):
    """Vincula un documento 07 con su original y el importe que ajusta."""

    comprobante = models.OneToOneField(
        Comprobante, on_delete=models.PROTECT, null=True, blank=True, related_name="nota_credito"
    )
    comprobante_referencia = models.ForeignKey(
        Comprobante, on_delete=models.PROTECT, related_name="notas_credito"
    )
    motivo = models.TextField()
    tipo_nota = models.CharField(max_length=5)
    monto_afectado = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_emision = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(monto_afectado__gt=0), name="nota_monto_positivo")
        ]

    def __str__(self):
        return f"NC ref: {self.comprobante_referencia} - Monto: {self.monto_afectado}"


class Membresia(models.Model):
    """Asigna un rol local a una empresa sin ampliar permisos globales."""

    ROLES = [("ADMIN", "Administrador"), ("EMISOR", "Emisor"), ("CONTADOR", "Contador")]
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membresias"
    )
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="membresias")
    rol = models.CharField(max_length=10, choices=ROLES)
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["usuario", "empresa"], name="membresia_usuario_empresa")
        ]

    def __str__(self):
        return f"{self.usuario} / {self.empresa_id}: {self.rol}"


class HistorialEstado(models.Model):
    """Registra cada transición con fecha y actor preservados."""

    comprobante = models.ForeignKey(Comprobante, on_delete=models.PROTECT, related_name="historial")
    anterior = models.CharField(max_length=15, blank=True)
    estado = models.CharField(max_length=15, choices=Comprobante.ESTADO_CHOICES)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)

    def __str__(self):
        return f"{self.comprobante_id}: {self.anterior} → {self.estado}"
