from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, ProductoViewSet, ComprobanteViewSet, NotaCreditoViewSet, ReportesViewSet

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'comprobantes', ComprobanteViewSet)
router.register(r'notas-credito', NotaCreditoViewSet)
router.register(r'reportes', ReportesViewSet, basename='reportes')

urlpatterns = [
    path('', include(router.urls)),
]