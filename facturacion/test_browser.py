"""Aceptación real en Chromium; ejecución optativa con RUN_BROWSER_TESTS=1."""

import os
import secrets
from io import StringIO
from pathlib import Path
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command


@skipUnless(
    os.getenv("RUN_BROWSER_TESTS") == "1",
    "Habilite RUN_BROWSER_TESTS=1 y prepare Playwright/Chromium.",
)
class NavegadorAceptacionTests(StaticLiveServerTestCase):
    """Recorre emisión, cálculos, crédito, descargas y navegación responsive."""

    def test_flujo_completo(self):
        from playwright.sync_api import expect, sync_playwright

        call_command("seed_demo", stdout=StringIO())
        password = secrets.token_urlsafe(20)
        usuario = get_user_model().objects.get(username="demo_emisor")
        usuario.set_password(password)
        usuario.save()
        capturas = Path("docs/evidencias")
        capturas.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            navegador = playwright.chromium.launch(headless=True)
            pagina = navegador.new_page(viewport={"width": 1440, "height": 1050})
            errores = []
            pagina.on("pageerror", lambda error: errores.append(str(error)))
            pagina.on("dialog", lambda dialog: dialog.accept())
            pagina.goto(self.live_server_url + "/login/")
            pagina.locator("#id_username").fill("demo_emisor")
            pagina.locator("#id_password").fill(password)
            pagina.get_by_role("button", name="Ingresar").click()
            expect(pagina.get_by_role("heading", name="Tu negocio, de un vistazo.")).to_be_visible()
            expect(pagina.locator(".chart-bar").first).to_be_visible()
            pagina.screenshot(path=str(capturas / "dashboard-desktop.png"), full_page=True)
            pagina.get_by_role("link", name="＋ Nuevo comprobante").click()
            pagina.locator("#cliente-busqueda").fill("201000")
            pagina.locator("#clientes-resultados button").first.click()
            pagina.locator("#producto-busqueda").fill("PROD-001")
            pagina.locator("#productos-resultados button").first.click()
            pagina.locator("#lineas tr").first.locator("input").nth(0).fill("2")
            pagina.locator("#lineas tr").first.locator("input").nth(2).fill("1")
            pagina.locator("#producto-busqueda").fill("PROD-003")
            pagina.locator("#productos-resultados button").first.click()
            expect(pagina.locator("#total-general")).to_have_text("S/ 91.00")
            pagina.get_by_role("button", name="Vista previa", exact=True).click()
            expect(pagina.locator("#preview-dialog")).to_be_visible()
            expect(pagina.locator("#preview-content")).to_contain_text("S/ 91.00")
            pagina.get_by_role("button", name="Cerrar vista previa").click()
            pagina.screenshot(path=str(capturas / "emision-desktop.png"), full_page=True)
            pagina.get_by_role("button", name="Emitir comprobante →", exact=True).click()
            pagina.wait_for_url("**/comprobantes/*/")
            expect(pagina.locator(".grand-total")).to_contain_text("91,00")
            expect(pagina.locator(".page-heading .status-badge")).to_have_text("Aceptado")
            pagina.get_by_role("link", name="Ver voucher / Imprimir").click()
            expect(pagina.locator(".voucher")).to_be_visible()
            pagina.evaluate(
                "() => { window.__printCalls = 0; window.print = () => { window.__printCalls++; }; }"
            )
            pagina.get_by_role("button", name="Imprimir", exact=True).click()
            self.assertEqual(pagina.evaluate("window.__printCalls"), 1)
            pagina.emulate_media(media="print")
            expect(pagina.locator("#sidebar")).to_be_hidden()
            expect(pagina.locator(".voucher")).to_be_visible()
            pagina.emulate_media(media="screen")
            pagina.screenshot(path=str(capturas / "voucher.png"), full_page=True)
            with pagina.expect_download() as download:
                pagina.get_by_role("link", name="Descargar PDF", exact=True).click()
            self.assertTrue(download.value.suggested_filename.endswith(".pdf"))
            pagina.go_back()
            pagina.get_by_role("link", name="Nota de crédito · Saldo", exact=False).click()
            expect(pagina.locator("#original-datos")).to_contain_text("91.00")
            pagina.locator("#monto-nota").fill("11.80")
            pagina.locator("#motivo-nota").fill("Devolución parcial verificada en navegador")
            pagina.get_by_role("button", name="Emitir nota de crédito →").click()
            pagina.wait_for_url("**/comprobantes/*/")
            expect(pagina.locator(".voucher")).to_contain_text(
                "Devolución parcial verificada en navegador"
            )
            pagina.get_by_role("link", name="Libro de ventas", exact=False).first.click()
            expect(pagina.get_by_role("heading", name="Libro de ventas.")).to_be_visible()
            with pagina.expect_download() as download:
                pagina.get_by_role("link", name="↓ Excel", exact=True).click()
            self.assertTrue(download.value.suggested_filename.endswith(".xlsx"))
            pagina.goto(self.live_server_url + "/comprobantes/?estado=RECHAZADO")
            pagina.get_by_role("link", name="Ver →", exact=True).first.click()
            pagina.get_by_role("button", name="Reenviar", exact=True).click()
            expect(pagina.locator(".page-heading .status-badge")).to_have_text("Aceptado")
            pagina.set_viewport_size({"width": 390, "height": 844})
            pagina.goto(self.live_server_url + "/")
            pagina.get_by_role("button", name="Abrir menú").click()
            expect(pagina.locator("#sidebar")).to_have_class("sidebar open")
            pagina.get_by_role("button", name="Cerrar menú").click()
            pagina.screenshot(path=str(capturas / "dashboard-mobile.png"), full_page=True)
            self.assertLessEqual(pagina.evaluate("document.documentElement.scrollWidth"), 390)
            self.assertEqual(errores, [])
            navegador.close()
