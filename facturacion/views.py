from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count

from .models import Empresa, SerieComprobante, Cliente, Producto, Comprobante, NotaCredito
from .serializers import (
    EmpresaSerializer, SerieComprobanteSerializer, ClienteSerializer,
    ProductoSerializer, ComprobanteSerializer, NotaCreditoSerializer
)
from .services import FacturacionService


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer


class ComprobanteViewSet(viewsets.ModelViewSet):
    queryset = Comprobante.objects.all().order_by('-fecha')
    serializer_class = ComprobanteSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        tipo = self.request.query_params.get('tipo')
        fecha_desde = self.request.query_params.get('fecha_desde')
        ruc_cliente = self.request.query_params.get('ruc_cliente')

        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if ruc_cliente:
            queryset = queryset.filter(cliente__num_doc=ruc_cliente)

        return queryset

    @action(detail=False, methods=['post'], url_path='emitir-factura')
    def emitir_factura(self, request):
        """POST /api/comprobantes/emitir-factura/"""
        return self._emitir(request, tipo_comp='01')

    @action(detail=False, methods=['post'], url_path='emitir-boleta')
    def emitir_boleta(self, request):
        """POST /api/comprobantes/emitir-boleta/"""
        return self._emitir(request, tipo_comp='03')

    def _emitir(self, request, tipo_comp):
        empresa_id = request.data.get('empresa_id')
        cliente_id = request.data.get('cliente_id')
        items = request.data.get('items', [])

        try:
            # Mapear productos
            items_procesados = []
            for item in items:
                prod = Producto.objects.get(id=item['producto_id'])
                items_procesados.append({
                    'producto': prod,
                    'cantidad': item['cantidad'],
                    'precio_unitario': item.get('precio_unitario', prod.precio_unitario),
                    'descuento': item.get('descuento', 0)
                })

            comprobante = FacturacionService.emitir_comprobante(
                tipo_comp=tipo_comp,
                empresa_id=empresa_id,
                cliente_id=cliente_id,
                items_data=items_procesados
            )
            serializer = self.get_serializer(comprobante)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='reenviar')
    def reenviar(self, request, pk=None):
        """POST /api/comprobantes/{id}/reenviar/"""
        comprobante = self.get_object()
        if comprobante.estado != 'RECHAZADO':
            return Response({'error': 'Solo se pueden reenviar comprobantes RECHAZADOS.'}, status=status.HTTP_400_BAD_REQUEST)

        FacturacionService.enviar_a_sunat(comprobante)
        serializer = self.get_serializer(comprobante)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NotaCreditoViewSet(viewsets.ModelViewSet):
    queryset = NotaCredito.objects.all()
    serializer_class = NotaCreditoSerializer

    def create(self, request, *args, **kwargs):
        comprobante_id = request.data.get('comprobante_id')
        motivo = request.data.get('motivo')
        tipo_nota = request.data.get('tipo_nota')
        monto = request.data.get('monto_afectado')

        try:
            nc = FacturacionService.emitir_nota_credito(
                comprobante_original_id=comprobante_id,
                motivo=motivo,
                tipo_nota=tipo_nota,
                monto_afectado=monto
            )
            serializer = self.get_serializer(nc)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReportesViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['get'], url_path='ventas-por-periodo')
    def ventas_por_periodo(self, request):
        """GET /api/reportes/ventas-por-periodo/?mes=XX&anio=YYYY"""
        mes = request.query_params.get('mes')
        anio = request.query_params.get('anio')

        queryset = Comprobante.objects.filter(estado='ACEPTADO')
        if mes:
            queryset = queryset.filter(fecha__month=mes)
        if anio:
            queryset = queryset.filter(fecha__year=anio)

        totales = queryset.aggregate(
            total_subtotal=Sum('subtotal'),
            total_igv=Sum('igv'),
            total_ventas=Sum('total'),
            cantidad_comprobantes=Count('id')
        )

        serializer = ComprobanteSerializer(queryset, many=True)
        return Response({
            'resumen': totales,
            'comprobantes': serializer.data
        })