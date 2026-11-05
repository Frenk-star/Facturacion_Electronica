"""Navegación de la aplicación mediante sesiones Django."""

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import web_views as web

urlpatterns = [
    path("configuracion/modo-emision/", web.cambiar_modo_emision, name="cambiar_modo_emision"),
    path("configuracion/", web.configuracion, name="configuracion"),
    path(
        "login/",
        LoginView.as_view(template_name="facturacion/login.html", redirect_authenticated_user=True),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", web.dashboard, name="dashboard"),
    path("empresa/seleccionar/", web.seleccionar_empresa, name="seleccionar_empresa"),
    path("emitir/", web.emitir, name="emitir"),
    path("comprobantes/", web.comprobantes, name="comprobantes"),
    path("comprobantes/<int:pk>/", web.comprobante_detalle, name="comprobante_detalle"),
    path("comprobantes/<int:pk>/voucher/", web.voucher, name="voucher"),
    path("notas-credito/", web.nota_credito, name="nota_credito"),
    path("clientes/", web.clientes, name="clientes"),
    path("clientes/consultar-ruc/", web.consulta_ruc, name="consulta_ruc"),
    path("clientes/consultar-dni/", web.consulta_dni, name="consulta_dni"),
    path("clientes/nuevo/", web.cliente_form, name="cliente_nuevo"),
    path("clientes/<int:pk>/", web.cliente_detalle, name="cliente_detalle"),
    path("clientes/<int:pk>/editar/", web.cliente_form, name="cliente_editar"),
    path("productos/", web.productos, name="productos"),
    path("productos/nuevo/", web.producto_form, name="producto_nuevo"),
    path("productos/<int:pk>/editar/", web.producto_form, name="producto_editar"),
    path("reportes/ventas/", web.reporte_ventas, name="reporte_ventas"),
]
