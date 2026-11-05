"""Pruebas de negocio, aislamiento, API y vistas sobre la implementación real."""

import secrets
from decimal import Decimal
from io import BytesIO, StringIO
from unittest.mock import patch
from xml.etree import ElementTree as ET

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone
from openpyxl import load_workbook
from rest_framework.test import APIClient

from .exceptions import MontoNotaCreditoExcedido
from .models import (
    Cliente,
    Comprobante,
    Empresa,
    Membresia,
    NotaCredito,
    Producto,
    SerieComprobante,
)
from .ose_mock import procesar
from .pdf_utils import generar_pdf
from .reportes import exportar_libro, libro_ventas
from .services import FacturacionService, calcular_linea, cambiar_estado, saldo_credito


class DatosSistemaMixin:
    """Fixtures comunes sin heredar ni repetir los escenarios de prueba."""

    @classmethod
    def setUpTestData(cls):
        cls.password_pruebas = secrets.token_urlsafe(24)
        cls.empresa = Empresa.objects.create(
            ruc="20601234567", razon_social="Empresa A", direccion="Lima", regimen_tributario="MYPE"
        )
        cls.otra = Empresa.objects.create(
            ruc="20601234568",
            razon_social="Empresa B",
            direccion="Cusco",
            regimen_tributario="MYPE",
        )
        for empresa in [cls.empresa, cls.otra]:
            for tipo, serie in [("F", "F001"), ("B", "B001"), ("FC", "FC01")]:
                SerieComprobante.objects.create(empresa=empresa, tipo=tipo, serie=serie)
        cls.cliente = Cliente.objects.create(
            empresa=cls.empresa,
            tipo_doc="RUC",
            num_doc="20100056781",
            razon_social="Cliente A",
            direccion="Lima",
        )
        cls.dni = Cliente.objects.create(
            empresa=cls.empresa,
            tipo_doc="DNI",
            num_doc="12345678",
            razon_social="Consumidor",
            direccion="Lima",
        )
        cls.ajeno = Cliente.objects.create(
            empresa=cls.otra,
            tipo_doc="RUC",
            num_doc="20100056782",
            razon_social="Cliente B",
            direccion="Cusco",
        )
        cls.producto = Producto.objects.create(
            empresa=cls.empresa,
            codigo="P1",
            descripcion="Producto gravado",
            unidad_medida="NIU",
            precio_unitario="118.00",
            afecto_igv=True,
        )
        cls.exento = Producto.objects.create(
            empresa=cls.empresa,
            codigo="P2",
            descripcion="No gravado",
            unidad_medida="NIU",
            precio_unitario="50.00",
            afecto_igv=False,
        )
        cls.producto_ajeno = Producto.objects.create(
            empresa=cls.otra,
            codigo="P1",
            descripcion="Producto B",
            unidad_medida="NIU",
            precio_unitario="118.00",
        )
        cls.emisor = get_user_model().objects.create_user(
            username="emisor", password=cls.password_pruebas
        )
        cls.contador = get_user_model().objects.create_user(
            username="contador", password=cls.password_pruebas
        )
        cls.admin = get_user_model().objects.create_user(
            username="administrador", password=cls.password_pruebas
        )
        for usuario, rol in [
            (cls.emisor, "EMISOR"),
            (cls.contador, "CONTADOR"),
            (cls.admin, "ADMIN"),
        ]:
            Membresia.objects.create(empresa=cls.empresa, usuario=usuario, rol=rol)

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(self.emisor)

    def items(self):
        return [
            {
                "producto": self.producto,
                "cantidad": Decimal("1.00"),
                "precio_unitario": Decimal("118.00"),
            }
        ]

    def emitir(self, **kwargs):
        return FacturacionService.emitir_comprobante(
            "01",
            self.empresa.pk,
            self.cliente.pk,
            kwargs.pop("items_data", self.items()),
            usuario=kwargs.pop("usuario", self.emisor),
            **kwargs,
        )

    def payload(self):
        return {
            "cliente_id": self.cliente.pk,
            "items": [{"producto_id": self.producto.pk, "cantidad": "1.00"}],
        }

    def credito(self, original, monto="11.80", **kwargs):
        return FacturacionService.emitir_nota_credito(
            original.pk,
            "Devolución",
            "07",
            monto,
            usuario=kwargs.pop("usuario", self.emisor),
            **kwargs,
        )


class SistemaTestCase(DatosSistemaMixin, TestCase):
    """Escenarios de aceptación con empresas y roles independientes."""

    def test_igv_incluido(self):
        self.assertEqual(
            calcular_linea("1", "118"),
            {"subtotal": Decimal("100"), "igv_linea": Decimal("18"), "total": Decimal("118")},
        )

    def test_igv_no_gravado(self):
        self.assertEqual(calcular_linea("2", "50", afecto_igv=False)["igv_linea"], 0)

    def test_descuento(self):
        self.assertEqual(calcular_linea("2", "118", "118")["subtotal"], Decimal("100"))

    def test_redondeo_comercial(self):
        self.assertEqual(calcular_linea("1", "1.005", afecto_igv=False)["total"], Decimal("1.01"))

    def test_importes_invalidos(self):
        for args in [
            ("0", "10", "0"),
            ("1", "-1", "0"),
            ("1", "10", "-1"),
            ("1", "10", "11"),
            ("NaN", "1", "0"),
        ]:
            with self.subTest(args=args), self.assertRaises(ValidationError):
                calcular_linea(*args)

    def test_factura_historial_logs_xml(self):
        documento = self.emitir()
        self.assertEqual((documento.subtotal, documento.igv, documento.total), (100, 18, 118))
        self.assertEqual(documento.estado, "ACEPTADO")
        self.assertEqual(
            list(documento.historial.values_list("estado", flat=True)),
            ["BORRADOR", "EMITIDO", "ENVIADO", "ACEPTADO"],
        )
        self.assertEqual(documento.logs_sunat.count(), 1)
        raiz = ET.fromstring(documento.xml_firmado)
        self.assertTrue(raiz.tag.endswith("Invoice"))
        self.assertIn("FIRMA MOCK", documento.xml_firmado)
        self.assertIn("20100056781", documento.xml_firmado)

    def test_factura_requiere_ruc(self):
        with self.assertRaises(ValidationError):
            FacturacionService.emitir_comprobante("01", self.empresa.pk, self.dni.pk, self.items())
        self.assertEqual(Comprobante.objects.count(), 0)

    def test_boleta_acepta_dni(self):
        documento = FacturacionService.emitir_comprobante(
            "03", self.empresa.pk, self.dni.pk, self.items()
        )
        self.assertEqual(documento.serie, "B001")
        self.assertIn("03", documento.xml_firmado)

    def test_mixto_totales(self):
        items = self.items() + [
            {
                "producto": self.exento,
                "cantidad": Decimal("2.00"),
                "precio_unitario": Decimal("50.00"),
                "descuento": Decimal("10.00"),
            }
        ]
        documento = FacturacionService.emitir_comprobante(
            "01", self.empresa.pk, self.cliente.pk, items
        )
        self.assertEqual((documento.subtotal, documento.igv, documento.total), (190, 18, 208))

    def test_correlativos_sucesivos(self):
        self.assertEqual([self.emitir().numero, self.emitir().numero], [1, 2])

    def test_rollback_no_consume_correlativo(self):
        with patch(
            "facturacion.xml_utils.generar_xml", side_effect=ValidationError("Fallo intencional")
        ):
            with self.assertRaises(ValidationError):
                self.emitir()
        self.assertEqual(Comprobante.objects.count(), 0)
        self.assertEqual(self.emitir().numero, 1)

    def test_borrador_sin_numero_y_emision(self):
        documento = self.emitir(borrador=True)
        self.assertIsNone(documento.numero)
        self.assertEqual(self.empresa.series.get(tipo="F").correlativo_actual, 0)
        documento = FacturacionService.emitir_borrador(documento, self.emisor)
        self.assertEqual(documento.numero, 1)
        with self.assertRaises(ValidationError):
            FacturacionService.emitir_borrador(documento)

    def test_idempotencia(self):
        a = self.emitir(clave_idempotencia="misma-solicitud")
        b = self.emitir(clave_idempotencia="misma-solicitud")
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(Comprobante.objects.count(), 1)

    def test_numeracion_independiente_por_empresa(self):
        a = self.emitir()
        b = FacturacionService.emitir_comprobante(
            "01",
            self.otra.pk,
            self.ajeno.pk,
            [{"producto": self.producto_ajeno, "cantidad": "1.00", "precio_unitario": "118.00"}],
        )
        self.assertEqual((a.numero, b.numero), (1, 1))

    def test_sin_serie_rollback(self):
        self.empresa.series.filter(tipo="F").delete()
        with self.assertRaises(ValidationError):
            self.emitir()
        self.assertFalse(Comprobante.objects.exists())

    def test_serie_seleccionada(self):
        SerieComprobante.objects.create(empresa=self.empresa, tipo="F", serie="F002")
        self.assertEqual(self.emitir(serie="F002").serie, "F002")

    def test_estado_invalido(self):
        with self.assertRaises(ValidationError):
            cambiar_estado(self.emitir(), "ENVIADO")

    def test_rechazo_reenvio_mismo_numero(self):
        documento = self.emitir(resultado_mock="RECHAZADO")
        numero = documento.numero
        FacturacionService.enviar_a_sunat(documento)
        self.assertEqual(
            (documento.estado, documento.numero, documento.logs_sunat.count()),
            ("ACEPTADO", numero, 2),
        )

    def test_mock_malformado_y_resultado_invalido(self):
        self.assertEqual(procesar("<invalido")["estado_respuesta"], "RECHAZADO")
        with self.assertRaises(ValidationError):
            procesar("<Invoice/>", "DESCONOCIDO")

    def test_credito_vinculado_xml(self):
        original = self.emitir()
        nota = self.credito(original)
        self.assertEqual(nota.comprobante.tipo, "07")
        self.assertIn("CreditNote", nota.comprobante.xml_firmado)
        self.assertIn("BillingReference", nota.comprobante.xml_firmado)
        self.assertEqual(saldo_credito(original), Decimal("106.20"))
        original.refresh_from_db()
        self.assertEqual(original.total, 118)

    def test_creditos_acumulados_y_cierre_impuestos(self):
        original = self.emitir()
        self.credito(original, "100.00")
        with self.assertRaises(MontoNotaCreditoExcedido):
            self.credito(original, "18.01")
        self.credito(original, "18.00")
        self.assertEqual(saldo_credito(original), 0)
        self.assertEqual(sum(n.comprobante.igv for n in original.notas_credito.all()), original.igv)

    def test_credito_idempotente(self):
        original = self.emitir()
        a = self.credito(original, clave_idempotencia="credito-1")
        b = self.credito(original, clave_idempotencia="credito-1")
        self.assertEqual(a.pk, b.pk)

    def test_credito_invalido(self):
        original = self.emitir(resultado_mock="RECHAZADO")
        with self.assertRaises(ValidationError):
            self.credito(original)
        original = self.emitir()
        for monto in ["0", "-1", "118.01"]:
            with self.assertRaises(ValidationError):
                self.credito(original, monto)
        with self.assertRaises(ValidationError):
            FacturacionService.emitir_nota_credito(original.pk, "", "99", "1")

    def test_credito_rechazado_reserva_saldo(self):
        original = self.emitir()
        self.credito(original, resultado_mock="RECHAZADO")
        self.assertEqual(saldo_credito(original), Decimal("106.20"))

    def test_aceptado_no_eliminable_ni_editable(self):
        documento = self.emitir()
        with self.assertRaises(ValidationError):
            documento.delete()
        with self.assertRaises((ValidationError, ProtectedError)):
            Comprobante.objects.filter(pk=documento.pk).delete()
        documento.total = Decimal("1")
        with self.assertRaises(ValidationError):
            documento.save()
        detalle = documento.detalles.first()
        with self.assertRaises(ValidationError):
            detalle.delete()
        detalle.cantidad = 10
        with self.assertRaises(ValidationError):
            detalle.save()

    def test_datos_historicos(self):
        documento = self.emitir()
        self.cliente.razon_social = "Nombre nuevo"
        self.cliente.save()
        self.producto.descripcion = "Descripción nueva"
        self.producto.save()
        documento.refresh_from_db()
        self.assertEqual(documento.datos_historicos["cliente"]["razon_social"], "Cliente A")
        self.assertEqual(documento.detalles.first().descripcion_historica, "Producto gravado")

    def test_validacion_modelo_documento(self):
        self.cliente.num_doc = "ABC"
        with self.assertRaises(ValidationError):
            self.cliente.full_clean()
        self.dni.num_doc = "123"
        with self.assertRaises(ValidationError):
            self.dni.full_clean()
        ce = Cliente(
            empresa=self.empresa,
            tipo_doc="CE",
            num_doc="ABC123",
            razon_social="Persona",
            direccion="Lima",
        )
        ce.full_clean()

    def test_unicidad_catalogo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Producto.objects.create(
                empresa=self.empresa,
                codigo="P1",
                descripcion="Duplicado",
                unidad_medida="NIU",
                precio_unitario=1,
            )

    def test_api_protegida(self):
        self.api.force_authenticate(None)
        self.assertEqual(self.api.get("/api/comprobantes/").status_code, 401)

    def test_api_factura_backend_recalcula(self):
        payload = self.payload()
        payload["total"] = "0.01"
        response = self.api.post("/api/facturas/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["total"], "118.00")

    def test_api_boleta_legacy(self):
        payload = self.payload()
        payload["cliente_id"] = self.dni.pk
        self.assertEqual(self.api.post("/api/boletas/", payload, format="json").status_code, 201)
        self.assertEqual(
            self.api.post(
                "/api/comprobantes/emitir-factura/", self.payload(), format="json"
            ).status_code,
            201,
        )

    def test_api_errores_validacion(self):
        for payload in [
            {},
            {"cliente_id": self.cliente.pk, "items": []},
            {"cliente_id": self.cliente.pk, "items": [{"producto_id": 1, "cantidad": "-1"}]},
        ]:
            response = self.api.post("/api/facturas/", payload, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn("codigo", response.data)

    def test_multiempresa_lectura_escritura(self):
        ajeno = FacturacionService.emitir_comprobante(
            "01",
            self.otra.pk,
            self.ajeno.pk,
            [{"producto": self.producto_ajeno, "cantidad": "1.00", "precio_unitario": "118.00"}],
        )
        self.assertEqual(self.api.get(f"/api/comprobantes/{ajeno.pk}/").status_code, 404)
        self.assertEqual(self.api.get(f"/api/comprobantes/{ajeno.pk}/pdf/").status_code, 404)
        self.assertEqual(
            self.api.get("/api/comprobantes/", HTTP_X_EMPRESA_ID=str(self.otra.pk)).status_code, 403
        )
        payload = self.payload()
        payload["empresa_id"] = self.otra.pk
        self.assertEqual(self.api.post("/api/facturas/", payload, format="json").status_code, 400)
        payload = self.payload()
        payload["cliente_id"] = self.ajeno.pk
        self.assertEqual(self.api.post("/api/facturas/", payload, format="json").status_code, 400)
        payload = self.payload()
        payload["items"][0]["producto_id"] = self.producto_ajeno.pk
        self.assertEqual(self.api.post("/api/facturas/", payload, format="json").status_code, 400)

    def test_contador_solo_lectura(self):
        self.api.force_authenticate(self.contador)
        self.assertEqual(self.api.get("/api/comprobantes/").status_code, 200)
        self.assertEqual(
            self.api.post("/api/facturas/", self.payload(), format="json").status_code, 403
        )
        self.assertEqual(self.api.post("/api/productos/", {}, format="json").status_code, 403)
        with self.assertRaises(ValidationError):
            self.emitir(usuario=self.contador)

    def test_series_solo_administrador(self):
        self.assertEqual(
            self.api.post(
                "/api/series/", {"tipo": "F", "serie": "F009"}, format="json"
            ).status_code,
            403,
        )
        self.api.force_authenticate(self.admin)
        response = self.api.post(
            "/api/series/", {"tipo": "F", "serie": "F009", "correlativo_actual": 999}, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["correlativo_actual"], 0)

    def test_jwt_y_refresh(self):
        self.api.force_authenticate(None)
        response = self.api.post(
            "/api/token/", {"username": "emisor", "password": self.password_pruebas}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.api.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        self.assertEqual(self.api.get("/api/clientes/").status_code, 200)
        self.assertEqual(
            self.api.post(
                "/api/token/refresh/", {"refresh": response.data["refresh"]}, format="json"
            ).status_code,
            200,
        )

    def test_api_filtros(self):
        documento = self.emitir()
        self.emitir(resultado_mock="RECHAZADO")
        hoy = timezone.localdate().isoformat()
        response = self.api.get(
            f"/api/comprobantes/?tipo=01&estado=ACEPTADO&fecha_desde={hoy}&fecha_hasta={hoy}&ruc_cliente={self.cliente.num_doc}&cliente={self.cliente.pk}"
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], documento.pk)
        self.assertEqual(self.api.get("/api/comprobantes/?fecha_desde=invalid").status_code, 400)
        self.assertEqual(
            self.api.get(
                "/api/comprobantes/?fecha_desde=2026-02-01&fecha_hasta=2026-01-01"
            ).status_code,
            400,
        )

    def test_api_reenvio_logs_descargas(self):
        documento = self.emitir(resultado_mock="RECHAZADO")
        self.assertEqual(
            self.api.post(
                f"/api/comprobantes/{documento.pk}/reenviar/", {}, format="json"
            ).status_code,
            200,
        )
        self.assertEqual(
            self.api.post(
                f"/api/comprobantes/{documento.pk}/reenviar/", {}, format="json"
            ).status_code,
            400,
        )
        self.assertEqual(len(self.api.get(f"/api/comprobantes/{documento.pk}/logs/").data), 2)
        self.assertEqual(
            self.api.get(f"/api/comprobantes/{documento.pk}/historial/").status_code, 200
        )
        pdf = self.api.get(f"/api/comprobantes/{documento.pk}/pdf/")
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        self.assertEqual(self.api.get(f"/api/comprobantes/{documento.pk}/xml/").status_code, 200)
        self.assertEqual(self.api.delete(f"/api/comprobantes/{documento.pk}/").status_code, 405)

    def test_api_borrador(self):
        payload = self.payload()
        payload["borrador"] = True
        response = self.api.post("/api/facturas/", payload, format="json")
        pk = response.data["id"]
        self.assertIsNone(response.data["numero"])
        self.assertEqual(self.api.get(f"/api/comprobantes/{pk}/xml/").status_code, 400)
        self.assertEqual(
            self.api.post(f"/api/comprobantes/{pk}/emitir/", {}, format="json").status_code, 200
        )

    def test_api_nota_credito(self):
        original = self.emitir()
        response = self.api.post(
            "/api/notas-credito/",
            {
                "comprobante_id": original.pk,
                "motivo": "Devolución",
                "tipo_nota": "07",
                "monto_afectado": "11.80",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(self.api.get("/api/notas-credito/").data["count"], 1)
        self.assertTrue(
            generar_pdf(NotaCredito.objects.get(pk=response.data["id"]).comprobante).startswith(
                b"%PDF"
            )
        )

    def test_api_crud_catalogos(self):
        payload = {
            "tipo_doc": "DNI",
            "num_doc": "87654321",
            "razon_social": "Nuevo",
            "direccion": "Lima",
        }
        response = self.api.post("/api/clientes/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        pk = response.data["id"]
        self.assertEqual(
            self.api.patch(
                f"/api/clientes/{pk}/", {"razon_social": "Editado"}, format="json"
            ).status_code,
            200,
        )
        self.assertEqual(self.api.get("/api/clientes/?q=8765&activo=true").data["count"], 1)
        self.assertEqual(self.api.delete(f"/api/clientes/{pk}/").status_code, 204)
        self.assertFalse(Cliente.objects.get(pk=pk).activo)
        payload["num_doc"] = "invalido"
        self.assertEqual(self.api.post("/api/clientes/", payload, format="json").status_code, 400)
        self.assertEqual(self.api.get("/api/productos/?q=gravado&activo=true").status_code, 200)

    def test_reportes_neto_sin_duplicacion(self):
        original = self.emitir()
        self.emitir(resultado_mock="RECHAZADO")
        self.credito(original)
        libro = libro_ventas(Comprobante.objects.filter(empresa=self.empresa), {})
        self.assertEqual(libro["resumen"]["total_ventas"], Decimal("106.20"))
        self.assertEqual(libro["resumen"]["cantidad_comprobantes"], 2)
        self.assertEqual(libro["resumen"]["rechazados"], 1)
        self.assertEqual(self.api.get("/api/reportes/ventas-por-periodo/").status_code, 200)
        self.assertEqual(self.api.get("/api/reportes/dashboard/").status_code, 200)
        self.assertEqual(self.api.get("/api/reportes/ventas-por-periodo/?mes=13").status_code, 400)
        self.assertEqual(
            self.api.get("/api/reportes/ventas-por-periodo/?formato=exe").status_code, 400
        )

    def test_exportaciones(self):
        self.emitir()
        libro = libro_ventas(Comprobante.objects.filter(empresa=self.empresa), {})
        csv = exportar_libro(libro, "csv")
        self.assertIn(b"118.00", csv.content)
        xlsx = exportar_libro(libro, "xlsx")
        workbook = load_workbook(BytesIO(xlsx.content))
        self.assertEqual(workbook.active["G2"].value, 118)
        for formato in ["csv", "xlsx"]:
            self.assertEqual(
                self.api.get(f"/api/reportes/ventas-por-periodo/?formato={formato}").status_code,
                200,
            )

    def test_paginas_web_y_voucher(self):
        documento = self.emitir()
        self.client.force_login(self.emisor)
        for url in [
            "/",
            "/emitir/",
            "/comprobantes/",
            f"/comprobantes/{documento.pk}/",
            f"/comprobantes/{documento.pk}/voucher/",
            "/notas-credito/",
            "/clientes/",
            "/clientes/nuevo/",
            f"/clientes/{self.cliente.pk}/",
            f"/clientes/{self.cliente.pk}/editar/",
            "/productos/",
            "/productos/nuevo/",
            f"/productos/{self.producto.pk}/editar/",
            "/reportes/ventas/",
            "/reportes/ventas/?formato=csv",
            "/reportes/ventas/?formato=xlsx",
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_formularios_web_y_busquedas(self):
        self.client.force_login(self.emisor)
        response = self.client.post(
            "/clientes/nuevo/",
            {
                "tipo_doc": "DNI",
                "num_doc": "87654321",
                "razon_social": "Persona",
                "direccion": "Lima",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.post(
            "/productos/nuevo/",
            {
                "codigo": "WEB",
                "descripcion": "Servicio web",
                "unidad_medida": "ZZ",
                "precio_unitario": "118",
                "afecto_igv": "on",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get("/clientes/?q=8765"), "Persona")
        self.assertContains(self.client.get("/productos/?q=WEB"), "Servicio web")
        self.assertEqual(
            self.client.post("/clientes/nuevo/", {"tipo_doc": "DNI", "num_doc": "xxx"}).status_code,
            200,
        )

    def test_web_sesiones_roles_empresa(self):
        self.assertEqual(self.client.get("/").status_code, 302)
        self.assertEqual(self.client.get("/login/").status_code, 200)
        self.assertEqual(
            self.client.post(
                "/login/", {"username": "emisor", "password": self.password_pruebas}
            ).status_code,
            302,
        )
        self.assertEqual(
            self.client.post("/empresa/seleccionar/", {"empresa_id": self.otra.pk}).status_code, 404
        )
        self.assertEqual(
            self.client.post("/empresa/seleccionar/", {"empresa_id": self.empresa.pk}).status_code,
            302,
        )
        self.assertEqual(self.client.post("/logout/").status_code, 302)
        self.client.force_login(self.contador)
        for url in ["/emitir/", "/notas-credito/", "/clientes/nuevo/", "/productos/nuevo/"]:
            self.assertEqual(self.client.get(url).status_code, 403)
        Membresia.objects.filter(usuario=self.contador).delete()
        self.assertEqual(self.client.get("/").status_code, 403)

    def test_swagger_schema(self):
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)
        self.assertEqual(self.client.get("/api/schema/").status_code, 200)

    def test_seed_repetible(self):
        salida = StringIO()
        call_command("seed_demo", stdout=salida)
        conteo = Comprobante.objects.count()
        call_command("seed_demo", stdout=salida)
        self.assertEqual(Comprobante.objects.count(), conteo)
