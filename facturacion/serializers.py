from rest_framework import serializers
from .models import Empresa, SerieComprobante, Cliente, Producto, Comprobante, DetalleComprobante, NotaCredito, LogEnvioSUNAT

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'

class SerieComprobanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SerieComprobante
        fields = '__all__'

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class DetalleComprobanteSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.descripcion')

    class Meta:
        model = DetalleComprobante
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario', 'descuento', 'igv_linea', 'subtotal']

class ComprobanteSerializer(serializers.ModelSerializer):
    detalles = DetalleComprobanteSerializer(many=True, read_only=True)
    cliente_nombre = serializers.ReadOnlyField(source='cliente.razon_social')
    cliente_num_doc = serializers.ReadOnlyField(source='cliente.num_doc')

    class Meta:
        model = Comprobante
        fields = [
            'id', 'serie', 'numero', 'fecha', 'cliente', 'cliente_nombre', 
            'cliente_num_doc', 'tipo', 'subtotal', 'igv', 'total', 'estado', 'detalles'
        ]

class EmitirComprobanteInputSerializer(serializers.Serializer):
    empresa_id = serializers.IntegerField()
    cliente_id = serializers.IntegerField()
    items = serializers.ListField(
        child=serializers.DictField(child=serializers.DecimalField(max_digits=12, decimal_places=2))
    )

class NotaCreditoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaCredito
        fields = '__all__'

class LogEnvioSUNATSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEnvioSUNAT
        fields = '__all__'