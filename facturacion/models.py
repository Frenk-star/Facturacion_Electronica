from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError

class Empresa(models.Model):
    ruc = models.CharField(max_length=11, unique=True, validators=[RegexValidator(r'^\d{11}$', 'El RUC debe tener 11 dígitos.')])
    razon_social = models.CharField(max_length=255)
    nombre_comercial = models.CharField(max_length=255, blank=True, null=True)
    direccion = models.TextField()
    regimen_tributario = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.ruc} - {self.razon_social}"

class SerieComprobante(models.Model):
    TIPO_CHOICES = [('F', 'Factura'), ('B', 'Boleta'), ('FC', 'Nota de Crédito/Débito')]
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES)
    serie = models.CharField(max_length=4)
    correlativo_actual = models.PositiveIntegerField(default=0)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='series')

    class Meta:
        unique_together = ('tipo', 'serie', 'empresa')

    def __str__(self):
        return f"{self.serie} ({self.get_tipo_display()})"

class Cliente(models.Model):
    TIPO_DOC_CHOICES = [('RUC', 'RUC'), ('DNI', 'DNI'), ('CE', 'Carné de Extranjería')]
    tipo_doc = models.CharField(max_length=3, choices=TIPO_DOC_CHOICES)
    num_doc = models.CharField(max_length=15, unique=True)
    razon_social = models.CharField(max_length=255)
    direccion = models.TextField()
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.num_doc} - {self.razon_social}"

class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    unidad_medida = models.CharField(max_length=10)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.00)])
    afecto_igv = models.BooleanField(default=True)

    def __str__(self):
        return f"[{self.codigo}] {self.descripcion}"

class Comprobante(models.Model):
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('EMITIDO', 'Emitido'),
        ('ENVIADO', 'Enviado'),
        ('ACEPTADO', 'Aceptado'),
        ('RECHAZADO', 'Rechazado'),
    ]
    TIPO_COMPROBANTE = [('01', 'Factura'), ('03', 'Boleta')]

    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='comprobantes', null=True, blank=True)
    serie = models.CharField(max_length=4)
    numero = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='comprobantes')
    tipo = models.CharField(max_length=2, choices=TIPO_COMPROBANTE)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    igv = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='BORRADOR')
    xml_firmado = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('serie', 'numero')

    def clean(self):
        super().clean()
        # Validación de Factura (01) exige Cliente con RUC de 11 dígitos
        if self.tipo == '01':
            if self.cliente.tipo_doc != 'RUC' or len(self.cliente.num_doc) != 11:
                raise ValidationError("Las facturas (tipo 01) solo pueden emitirse a clientes con RUC de 11 dígitos.")

    def __str__(self):
        return f"{self.serie}-{self.numero:08d} ({self.estado})"

class DetalleComprobante(models.Model):
    comprobante = models.ForeignKey(Comprobante, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    igv_linea = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

class LogEnvioSUNAT(models.Model):
    comprobante = models.ForeignKey(Comprobante, on_delete=models.CASCADE, related_name='logs_sunat')
    fecha_envio = models.DateTimeField(auto_now_add=True)
    estado_respuesta = models.CharField(max_length=20)
    codigo_respuesta = models.CharField(max_length=10)
    descripcion = models.TextField()

class NotaCredito(models.Model):
    comprobante_referencia = models.ForeignKey(Comprobante, on_delete=models.PROTECT, related_name='notas_credito')
    motivo = models.TextField()
    tipo_nota = models.CharField(max_length=5)
    monto_afectado = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_emision = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"NC ref: {self.comprobante_referencia} - Monto: {self.monto_afectado}"