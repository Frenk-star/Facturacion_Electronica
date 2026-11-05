"""Escenarios de administración local, restricciones y casos extremos."""

import secrets
from decimal import Decimal

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase

from .models import Comprobante, Empresa, Membresia
from .tests import DatosSistemaMixin


class AdministracionTests(DatosSistemaMixin, TestCase):
    """Reutiliza fixtures del sistema y añade verificaciones administrativas."""

    def test_usuarios_administracion_local(self):
        self.assertEqual(self.api.get("/api/usuarios/").status_code, 403)
        self.api.force_authenticate(self.admin)
        datos = {
            "username": "nuevo_emisor",
            "email": "persona@example.com",
            "password": secrets.token_urlsafe(24),
            "rol": "EMISOR",
        }
        response = self.api.post("/api/usuarios/", datos, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotIn("password", response.data)
        usuario = get_user_model().objects.get(pk=response.data["id"])
        self.assertTrue(usuario.check_password(datos["password"]))
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertEqual(
            self.api.patch(
                f"/api/usuarios/{usuario.pk}/",
                {"rol": "CONTADOR", "first_name": "Nuevo"},
                format="json",
            ).status_code,
            200,
        )
        self.assertEqual(Membresia.objects.get(usuario=usuario).rol, "CONTADOR")
        self.assertEqual(self.api.delete(f"/api/usuarios/{usuario.pk}/").status_code, 204)
        self.assertFalse(Membresia.objects.get(usuario=usuario).activo)
        self.assertEqual(
            self.api.post("/api/usuarios/", {"username": "sin_clave"}, format="json").status_code,
            400,
        )
        self.assertEqual(
            self.api.post(
                "/api/usuarios/", {**datos, "username": "debil", "password": "123"}, format="json"
            ).status_code,
            400,
        )

    def test_cuenta_compartida_no_modificable_localmente(self):
        Membresia.objects.create(usuario=self.emisor, empresa=self.otra, rol="EMISOR")
        self.api.force_authenticate(self.admin)
        self.assertEqual(
            self.api.patch(
                f"/api/usuarios/{self.emisor.pk}/",
                {"password": secrets.token_urlsafe(24)},
                format="json",
            ).status_code,
            400,
        )

    def test_configuracion_web(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get("/configuracion/"), "Crear cuenta")
        self.client.force_login(self.emisor)
        self.assertEqual(self.client.get("/configuracion/").status_code, 403)

    def test_empresa_edicion(self):
        self.api.force_authenticate(self.admin)
        response = self.api.patch(
            f"/api/empresas/{self.empresa.pk}/", {"nombre_comercial": "Nuevo nombre"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.api.patch(
                f"/api/empresas/{self.otra.pk}/", {"nombre_comercial": "Ajena"}, format="json"
            ).status_code,
            404,
        )

    def test_admin_global_solo_superusuario(self):
        modelo_admin = admin.site._registry[Empresa]
        request = RequestFactory().get("/admin/")
        request.user = self.admin
        self.assertFalse(modelo_admin.has_view_permission(request))
        self.assertFalse(modelo_admin.has_module_permission(request))
        self.assertFalse(modelo_admin.has_change_permission(request))
        self.assertFalse(modelo_admin.has_delete_permission(request))
        self.assertFalse(modelo_admin.has_add_permission(request))
        self.admin.is_superuser = True
        self.assertTrue(modelo_admin.has_view_permission(request))
        self.assertTrue(modelo_admin.has_module_permission(request))
        auditoria = admin.site._registry[Comprobante]
        self.assertFalse(auditoria.has_add_permission(request))
        self.assertFalse(auditoria.has_change_permission(request))
        self.assertFalse(auditoria.has_delete_permission(request))

    def test_decimales_sqlite_no_producen_falsos_rechazos(self):
        for precio in ["0.10", "0.30", "1.01", "7.99", "9.99", "18.90", "28.50"]:
            documento = self.emitir(
                items_data=[
                    {
                        "producto": self.producto,
                        "cantidad": Decimal("1.00"),
                        "precio_unitario": Decimal(precio),
                    }
                ]
            )
            self.assertEqual(documento.total, Decimal(precio))

    def test_creditos_pequenos_no_exceden_impuestos(self):
        original = self.emitir(
            items_data=[
                {
                    "producto": self.producto,
                    "cantidad": Decimal("1.00"),
                    "precio_unitario": Decimal("0.12"),
                }
            ]
        )
        self.credito(original, "0.04")
        self.credito(original, "0.04")
        self.credito(original, "0.04")
        creditos = original.notas_credito.select_related("comprobante")
        self.assertEqual(sum(n.comprobante.igv for n in creditos), original.igv)
        self.assertTrue(all(n.comprobante.igv >= 0 for n in creditos))

    def test_modelo_rechaza_transicion_directa(self):
        documento = self.emitir()
        documento.estado = "BORRADOR"
        with self.assertRaises(ValidationError):
            documento.save()
        documento.refresh_from_db()
        from django.utils import timezone

        documento.fecha = timezone.now()
        with self.assertRaises(ValidationError):
            documento.save()

    def test_claves_no_reutilizables_con_otros_datos(self):
        self.emitir(clave_idempotencia="venta-1")
        with self.assertRaises(ValidationError):
            self.emitir(
                clave_idempotencia="venta-1",
                items_data=[
                    {
                        "producto": self.producto,
                        "cantidad": Decimal("2.00"),
                        "precio_unitario": Decimal("118.00"),
                    }
                ],
            )
        original = self.emitir()
        self.credito(original, clave_idempotencia="nota-1")
        with self.assertRaises(ValidationError):
            self.credito(original, "10.00", clave_idempotencia="nota-1")

    def test_csrf_sesion_exigido_en_mutaciones(self):
        from django.test import Client

        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.emisor)
        response = cliente.post("/api/facturas/", self.payload(), content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_duplicado_membresia_es_error_coherente(self):
        self.api.force_authenticate(self.admin)
        response = self.api.post(
            "/api/membresias/", {"usuario": self.emisor.pk, "rol": "CONTADOR"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("codigo", response.data)

    def test_empresa_invalida_no_genera_error_interno(self):
        self.assertEqual(
            self.api.get("/api/comprobantes/", HTTP_X_EMPRESA_ID="invalida").status_code, 403
        )
        self.client.force_login(self.emisor)
        self.assertEqual(
            self.client.post("/empresa/seleccionar/", {"empresa_id": "invalida"}).status_code, 403
        )
