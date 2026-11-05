"""Autorización por membresía explícita y empresa activa."""

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Empresa, Membresia


def empresa_autorizada(request):
    """Resuelve el ámbito sin confiar en identificadores enviados en el cuerpo."""
    empresa_id = request.headers.get("X-Empresa-ID") or request.session.get("empresa_id")
    if empresa_id is not None and (not str(empresa_id).isascii() or not str(empresa_id).isdigit()):
        raise PermissionDenied("El identificador de empresa debe ser numérico.")
    empresas = (
        Empresa.objects.all()
        if request.user.is_superuser
        else Empresa.objects.filter(membresias__usuario=request.user, membresias__activo=True)
    )
    empresa = (
        empresas.filter(pk=empresa_id).first() if empresa_id else empresas.order_by("pk").first()
    )
    if empresa is None:
        raise PermissionDenied("No tiene una empresa autorizada. Solicite una membresía.")
    return empresa


def rol_usuario(usuario, empresa):
    """Obtiene el rol en la empresa; superusuarios tienen alcance global."""
    if usuario.is_superuser:
        return "ADMIN"
    return (
        Membresia.objects.filter(usuario=usuario, empresa=empresa, activo=True)
        .values_list("rol", flat=True)
        .first()
    )


class PermisoEmpresa(BasePermission):
    """Permite lectura a contadores y escritura a emisores y administradores."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        request.empresa = empresa_autorizada(request)
        rol = rol_usuario(request.user, request.empresa)
        if getattr(view, "solo_admin", False) and request.method not in SAFE_METHODS:
            return rol == "ADMIN"
        return request.method in SAFE_METHODS or rol in {"ADMIN", "EMISOR"}
