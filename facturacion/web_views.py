"""Controladores HTML. La lógica tributaria permanece en los servicios."""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework.exceptions import APIException

from .forms import ClienteForm, ProductoForm
from .models import Cliente, Comprobante, Empresa, Producto
from .permissions import empresa_autorizada, rol_usuario
from .reportes import exportar_libro, libro_ventas
from .services import saldo_credito
from .views import filtrar_comprobantes


def contexto_empresa(vista):
    """Exige sesión y añade exclusivamente empresas accesibles al usuario."""

    @login_required
    @wraps(vista)
    def protegida(request, *args, **kwargs):
        try:
            request.empresa = empresa_autorizada(request)
        except APIException as exc:
            return render(
                request, "facturacion/sin_empresa.html", {"mensaje": str(exc)}, status=403
            )
        request.rol_empresa = rol_usuario(request.user, request.empresa)
        return vista(request, *args, **kwargs)

    return protegida


def _render(request, plantilla, **contexto):
    empresas = (
        Empresa.objects.all()
        if request.user.is_superuser
        else Empresa.objects.filter(membresias__usuario=request.user, membresias__activo=True)
    )
    return render(
        request,
        f"facturacion/{plantilla}.html",
        {
            "empresa_activa": request.empresa,
            "empresas": empresas,
            "puede_emitir": request.rol_empresa in {"ADMIN", "EMISOR"},
            "rol": request.rol_empresa,
            **contexto,
        },
    )


@login_required
@require_POST
def seleccionar_empresa(request):
    empresa_id = request.POST.get("empresa_id", "")
    if not empresa_id.isascii() or not empresa_id.isdigit():
        raise PermissionDenied("Seleccione una empresa válida.")
    empresas = (
        Empresa.objects.all()
        if request.user.is_superuser
        else Empresa.objects.filter(membresias__usuario=request.user, membresias__activo=True)
    )
    empresa = get_object_or_404(empresas, pk=empresa_id)
    request.session["empresa_id"] = empresa.pk
    return redirect("dashboard")


@contexto_empresa
def dashboard(request):
    hoy = timezone.localdate()
    documentos = Comprobante.objects.filter(empresa=request.empresa)
    mes = documentos.filter(fecha__year=hoy.year, fecha__month=hoy.month)
    libro = libro_ventas(documentos, {})
    estados = dict(mes.values_list("estado").annotate(cantidad=Count("id")))
    return _render(
        request,
        "dashboard",
        titulo="Resumen del negocio",
        libro=libro,
        facturas=mes.filter(tipo="01").count(),
        boletas=mes.filter(tipo="03").count(),
        aceptados=estados.get("ACEPTADO", 0),
        rechazados=estados.get("RECHAZADO", 0),
        pendientes=mes.filter(estado__in=["BORRADOR", "EMITIDO", "ENVIADO"]).count(),
        documentos=documentos.select_related("cliente").order_by("-fecha")[:8],
    )


@contexto_empresa
def configuracion(request):
    """Presenta mantenimiento de empresa, series y cuentas para administradores."""
    if request.rol_empresa != "ADMIN":
        raise PermissionDenied
    return _render(
        request,
        "configuracion",
        titulo="Configuración",
        series=request.empresa.series.all(),
        membresias=request.empresa.membresias.select_related("usuario").all(),
    )


@contexto_empresa
def emitir(request):
    if request.rol_empresa not in {"ADMIN", "EMISOR"}:
        raise PermissionDenied
    return _render(
        request,
        "emitir",
        titulo="Emitir comprobante",
        series=request.empresa.series.exclude(tipo="FC"),
    )


@contexto_empresa
def comprobantes(request):
    documentos = (
        Comprobante.objects.filter(empresa=request.empresa)
        .select_related("cliente")
        .order_by("-fecha", "-pk")
    )
    try:
        documentos = filtrar_comprobantes(documentos, request.GET)
    except APIException as exc:
        messages.error(request, str(exc.detail))
        documentos = documentos.none()
    return _render(
        request,
        "comprobantes",
        titulo="Comprobantes",
        pagina=Paginator(documentos, 20).get_page(request.GET.get("page")),
        estados=Comprobante.ESTADO_CHOICES,
        tipos=Comprobante.TIPO_COMPROBANTE,
    )


def _documento(request, pk):
    return get_object_or_404(
        Comprobante.objects.select_related("empresa", "cliente").prefetch_related("detalles"),
        pk=pk,
        empresa=request.empresa,
    )


@contexto_empresa
def comprobante_detalle(request, pk):
    documento = _documento(request, pk)
    return _render(
        request,
        "comprobante_detalle",
        titulo="Detalle del comprobante",
        documento=documento,
        saldo=saldo_credito(documento),
    )


@contexto_empresa
def voucher(request, pk):
    return _render(
        request, "voucher", titulo="Voucher imprimible", documento=_documento(request, pk)
    )


@contexto_empresa
def nota_credito(request):
    if request.rol_empresa not in {"ADMIN", "EMISOR"}:
        raise PermissionDenied
    return _render(
        request,
        "nota_credito",
        titulo="Emitir nota de crédito",
        original_id=request.GET.get("original", ""),
    )


def _catalogo(request, modelo, plantilla, titulo):
    registros = modelo.objects.filter(empresa=request.empresa).order_by("pk")
    termino = request.GET.get("q", "")
    campos = ["num_doc", "razon_social"] if modelo == Cliente else ["codigo", "descripcion"]
    if termino:
        registros = registros.filter(
            Q(**{f"{campos[0]}__icontains": termino}) | Q(**{f"{campos[1]}__icontains": termino})
        )
    return _render(
        request,
        plantilla,
        titulo=titulo,
        pagina=Paginator(registros, 20).get_page(request.GET.get("page")),
    )


@contexto_empresa
def clientes(request):
    return _catalogo(request, Cliente, "clientes", "Clientes")


@contexto_empresa
def productos(request):
    return _catalogo(request, Producto, "productos", "Productos y servicios")


def _formulario(request, modelo, formulario, plantilla, destino, pk):
    if request.rol_empresa not in {"ADMIN", "EMISOR"}:
        raise PermissionDenied
    objeto = (
        get_object_or_404(modelo, pk=pk, empresa=request.empresa)
        if pk
        else modelo(empresa=request.empresa)
    )
    form = formulario(request.POST or None, instance=objeto)
    if request.method == "POST" and form.is_valid():
        objeto = form.save(commit=False)
        try:
            objeto.full_clean()
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            objeto.save()
            messages.success(request, "Registro guardado correctamente.")
            return redirect(destino)
    return _render(
        request, plantilla, titulo="Editar registro" if pk else "Nuevo registro", form=form
    )


@contexto_empresa
def cliente_form(request, pk=None):
    return _formulario(request, Cliente, ClienteForm, "cliente_form", "clientes", pk)


@contexto_empresa
def producto_form(request, pk=None):
    return _formulario(request, Producto, ProductoForm, "producto_form", "productos", pk)


@contexto_empresa
def cliente_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk, empresa=request.empresa)
    documentos = cliente.comprobantes.filter(empresa=request.empresa).order_by("-fecha")
    return _render(
        request,
        "cliente_detalle",
        titulo="Historial del cliente",
        cliente=cliente,
        pagina=Paginator(documentos, 20).get_page(request.GET.get("page")),
    )


@contexto_empresa
def reporte_ventas(request):
    try:
        libro = libro_ventas(Comprobante.objects.filter(empresa=request.empresa), request.GET)
    except APIException as exc:
        messages.error(request, str(exc.detail))
        libro = libro_ventas(Comprobante.objects.none(), {})
    if request.GET.get("formato") in {"csv", "xlsx"}:
        return exportar_libro(libro, request.GET["formato"])
    return _render(request, "reporte_ventas", titulo="Libro de ventas", libro=libro)
