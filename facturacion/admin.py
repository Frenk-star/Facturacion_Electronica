"""Administración global reservada a superusuarios; documentos de solo lectura."""

from django.contrib import admin

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


class AdministracionGlobal(admin.ModelAdmin):
    """Impide que permisos staff accidentales eludan el aislamiento empresarial."""

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class AuditoriaAdmin(AdministracionGlobal):
    """Permite inspección, nunca cambios manuales en evidencia de emisión."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class DetalleComprobanteInline(admin.TabularInline):
    model = DetalleComprobante
    extra = 0
    can_delete = False
    readonly_fields = tuple(campo.name for campo in DetalleComprobante._meta.fields)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Empresa)
class EmpresaAdmin(AdministracionGlobal):
    list_display = ("ruc", "razon_social", "regimen_tributario")
    search_fields = ("ruc", "razon_social")


@admin.register(SerieComprobante)
class SerieComprobanteAdmin(AdministracionGlobal):
    list_display = ("empresa", "tipo", "serie", "correlativo_actual")
    list_filter = ("tipo", "empresa")
    readonly_fields = ("correlativo_actual",)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and obj is None

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Cliente)
class ClienteAdmin(AdministracionGlobal):
    list_display = ("num_doc", "tipo_doc", "razon_social", "email", "empresa")
    search_fields = ("num_doc", "razon_social")
    list_filter = ("tipo_doc", "empresa")


@admin.register(Producto)
class ProductoAdmin(AdministracionGlobal):
    list_display = ("codigo", "descripcion", "precio_unitario", "afecto_igv", "empresa")
    search_fields = ("codigo", "descripcion")
    list_filter = ("afecto_igv", "empresa")


@admin.register(Comprobante)
class ComprobanteAdmin(AuditoriaAdmin):
    list_display = ("serie", "numero", "tipo", "cliente", "fecha", "total", "estado", "empresa")
    list_filter = ("estado", "tipo", "fecha", "empresa")
    search_fields = ("serie", "numero", "cliente__razon_social", "cliente__num_doc")
    inlines = [DetalleComprobanteInline]


@admin.register(NotaCredito)
class NotaCreditoAdmin(AuditoriaAdmin):
    list_display = ("comprobante_referencia", "tipo_nota", "monto_afectado", "fecha_emision")


@admin.register(LogEnvioSUNAT)
class LogEnvioSUNATAdmin(AuditoriaAdmin):
    list_display = ("comprobante", "fecha_envio", "estado_respuesta", "codigo_respuesta")
    list_filter = ("estado_respuesta",)


admin.site.register(Membresia, AdministracionGlobal)
admin.site.register(HistorialEstado, AuditoriaAdmin)
admin.site.site_header = "Nexo · Administración global"
