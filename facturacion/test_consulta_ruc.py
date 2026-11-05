"""Contrato del proveedor y protección de la consulta externa."""

import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

from django.test import TestCase, override_settings

from .consulta_ruc import ErrorConsultaRuc, consultar_ruc
from .tests import DatosSistemaMixin


class ConsultaRucTests(DatosSistemaMixin, TestCase):
    @override_settings(RUC_API_TOKEN="")
    @patch("facturacion.consulta_ruc.urlopen")
    def test_sin_token_no_consulta(self, abrir):
        with self.assertRaises(ErrorConsultaRuc):
            consultar_ruc("20100047218")
        abrir.assert_not_called()

    @override_settings(RUC_API_TOKEN="token-prueba")
    @patch("facturacion.consulta_ruc.urlopen")
    def test_respuesta_y_errores(self, abrir):
        datos = {"ruc": "20100047218", "razon_social": "Empresa real", "direccion": None}
        abrir.return_value = BytesIO(json.dumps({"success": True, "data": datos}).encode())
        resultado = consultar_ruc(datos["ruc"])
        self.assertEqual(resultado["direccion"], "")
        self.assertEqual(resultado["razon_social"], "Empresa real")
        self.assertEqual(abrir.call_args.args[0].get_header("Authorization"), "Bearer token-prueba")
        for codigo in [401, 403, 404, 422, 429, 500]:
            abrir.side_effect = HTTPError("https://consultaderuc.pe", codigo, "", {}, None)
            with self.assertRaises(ErrorConsultaRuc) as error:
                consultar_ruc(datos["ruc"])
            self.assertEqual(error.exception.status, codigo if codigo in {404, 422, 429} else 503)

    @override_settings(RUC_API_TOKEN="token-prueba")
    @patch("facturacion.consulta_ruc.urlopen")
    def test_documentos_y_respuestas_invalidas(self, abrir):
        for documento in ["123", "a" * 11, "２０１０００４７２１８"]:
            with self.assertRaises(ErrorConsultaRuc):
                consultar_ruc(documento)
        abrir.assert_not_called()
        for payload in [{"success": True, "data": None}, {"success": False}, []]:
            abrir.return_value = BytesIO(json.dumps(payload).encode())
            with self.assertRaises(ErrorConsultaRuc):
                consultar_ruc("20100047218")

    @patch("facturacion.web_views.consultar_ruc")
    def test_permisos_metodo_y_pantalla(self, consulta):
        url = "/clientes/consultar-ruc/"
        self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(self.contador)
        self.assertEqual(self.client.post(url).status_code, 403)
        consulta.assert_not_called()
        self.client.force_login(self.emisor)
        self.assertEqual(self.client.get(url).status_code, 405)
        consulta.return_value = {"ruc": "20100047218", "razon_social": "Empresa"}
        self.assertEqual(self.client.post(url, {"ruc": "20100047218"}).status_code, 200)
        pagina = self.client.get("/clientes/nuevo/")
        self.assertContains(pagina, 'id="modo-real" data-url=')
        self.assertContains(pagina, "Consultar RUC real")

    def test_modo_real_no_se_activa_sin_integracion(self):
        url = "/configuracion/modo-emision/"
        self.client.force_login(self.emisor)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 405)
        respuesta = self.client.post(url)
        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(respuesta.json()["modo"], "PRUEBAS")
        self.assertIn("certificado digital", respuesta.json()["detail"])
