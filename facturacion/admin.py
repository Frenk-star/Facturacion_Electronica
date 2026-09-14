from django.contrib import admin
from .models import Empresa, SerieComprobante, Cliente, Producto, Comprobante, DetalleComprobante, LogEnvioSUNAT, NotaCredito


class DetalleComprobanteInline(admin.TabularInline):
    model = DetalleComprobante
    extra = 0
    readonly_fields = ('igv_linea', 'subtotal')


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('ruc', 'razon_social', 'regimen_tributario')
    search_fields = ('ruc', 'razon_social')


@admin.register(SerieComprobante)
class SerieComprobanteAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'tipo', 'serie', 'correlativo_actual')
    list_filter = ('tipo', 'empresa')


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('num_doc', 'tipo_doc', 'razon_social', 'email')
    search_fields = ('num_doc', 'razon_social')
    list_filter = ('tipo_doc',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'precio_unitario', 'afecto_igv')
    search_fields = ('codigo', 'descripcion')
    list_filter = ('afecto_igv',)


@admin.register(Comprobante)
class ComprobanteAdmin(admin.ModelAdmin):
    list_display = ('serie', 'numero', 'tipo', 'cliente', 'fecha', 'total', 'estado')
    list_filter = ('estado', 'tipo', 'fecha')
    search_fields = ('serie', 'numero', 'cliente__razon_social', 'cliente__num_doc')
    inlines = [DetalleComprobanteInline]


@admin.register(NotaCredito)
class NotaCreditoAdmin(admin.ModelAdmin):
    list_display = ('comprobante_referencia', 'tipo_nota', 'monto_afectado', 'fecha_emision')


@admin.register(LogEnvioSUNAT)
class LogEnvioSUNATAdmin(admin.ModelAdmin):
    list_display = ('comprobante', 'fecha_envio', 'estado_respuesta', 'codigo_respuesta')
    list_filter = ('estado_respuesta',)