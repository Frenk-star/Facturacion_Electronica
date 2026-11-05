"""Rutas REST conservadas y ampliadas."""

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    ClienteViewSet,
    ComprobanteViewSet,
    EmpresaViewSet,
    MembresiaViewSet,
    NotaCreditoViewSet,
    ProductoViewSet,
    ReportesViewSet,
    SerieComprobanteViewSet,
    UsuarioViewSet,
)

router = DefaultRouter()
router.register("clientes", ClienteViewSet)
router.register("productos", ProductoViewSet)
router.register("comprobantes", ComprobanteViewSet)
router.register("notas-credito", NotaCreditoViewSet)
router.register("reportes", ReportesViewSet, basename="reportes")
router.register("empresas", EmpresaViewSet)
router.register("series", SerieComprobanteViewSet)
router.register("membresias", MembresiaViewSet)
router.register("usuarios", UsuarioViewSet)
urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("facturas/", ComprobanteViewSet.as_view({"post": "emitir_factura"}), name="facturas"),
    path("boletas/", ComprobanteViewSet.as_view({"post": "emitir_boleta"}), name="boletas"),
    path("", include(router.urls)),
]
