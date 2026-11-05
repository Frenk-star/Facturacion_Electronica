"""Verifica contrato, permisos y fallos de la consulta DNI sin consumir cuota."""

import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from django.test import Client, TestCase, override_settings

from .consulta_dni import ErrorConsultaDni, consultar_dni
from .tests import DatosSistemaMixin


class ConsultaDniTests(DatosSistemaMixin, TestCase):
    @override_settings(DNI_API_TOKEN="")
    @patch("facturacion.consulta_dni.urlopen")
    def test_validacion_y_token(self, abrir):
        for dni in ["123", "abcdefgh", "１２３４５６７８"]:
            with self.assertRaises(ErrorConsultaDni) as error:
                consultar_dni(dni)
            self.assertEqual(error.exception.status, 400)
        with self.assertRaises(ErrorConsultaDni):
            consultar_dni("00000001")
        abrir.assert_not_called()

    @override_settings(DNI_API_TOKEN="token-prueba")
    @patch("facturacion.consulta_dni.urlopen")
    def test_contrato_y_minimizacion(self, abrir):
        abrir.return_value = BytesIO(
            json.dumps(
                {
                    "success": True,
                    "data": {
                        "numero": "00000001",
                        "nombre_completo": "CLIENTE DE PRUEBA",
                        "direccion": "Privada",
                        "fecha_nacimiento": "Privada",
                    },
                }
            ).encode()
        )
        resultado = consultar_dni("00000001")
        self.assertEqual(resultado["razon_social"], "CLIENTE DE PRUEBA")
        self.assertEqual(set(resultado), {"dni", "razon_social", "fuente"})
        self.assertTrue(abrir.call_args.args[0].full_url.endswith("/00000001"))
        self.assertEqual(abrir.call_args.args[0].get_header("Authorization"), "Bearer token-prueba")

    @override_settings(DNI_API_TOKEN="token-prueba")
    @patch("facturacion.consulta_dni.urlopen")
    def test_respuestas_incompletas_y_red(self, abrir):
        for payload in [
            [],
            {"success": False},
            {"success": True, "data": None},
            {"success": True, "data": {"numero": "99999999"}},
            {"success": True, "data": {"numero": "00000001", "nombre_completo": ""}},
        ]:
            abrir.return_value = BytesIO(json.dumps(payload).encode())
            with self.assertRaises(ErrorConsultaDni):
                consultar_dni("00000001")
        for codigo in [400, 401, 403, 404, 422, 429, 500]:
            abrir.side_effect = HTTPError("https://api.factiliza.com", codigo, "", {}, None)
            with self.assertRaises(ErrorConsultaDni) as error:
                consultar_dni("00000001")
            self.assertEqual(
                error.exception.status, codigo if codigo in {400, 404, 422, 429} else 503
            )
        for fallo in [URLError("sin red"), TimeoutError(), ValueError()]:
            abrir.side_effect = fallo
            with self.assertRaises(ErrorConsultaDni) as error:
                consultar_dni("00000001")
            self.assertEqual(error.exception.status, 502)

    @patch("facturacion.web_views.consultar_dni")
    def test_acceso_csrf_y_pantalla(self, consulta):
        url = "/clientes/consultar-dni/"
        self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(self.contador)
        self.assertEqual(self.client.post(url).status_code, 403)
        consulta.assert_not_called()
        self.client.force_login(self.emisor)
        self.assertEqual(self.client.get(url).status_code, 405)
        consulta.return_value = {"dni": "00000001", "razon_social": "CLIENTE"}
        self.assertEqual(self.client.post(url, {"dni": "00000001"}).status_code, 200)
        consulta.assert_called_once_with("00000001")
        consulta.side_effect = ErrorConsultaDni("Límite alcanzado", 429)
        self.assertEqual(self.client.post(url, {"dni": "00000001"}).status_code, 429)
        seguro = Client(enforce_csrf_checks=True)
        seguro.force_login(self.emisor)
        self.assertEqual(seguro.post(url, {"dni": "00000001"}).status_code, 403)
        self.assertContains(self.client.get("/clientes/nuevo/"), "Consultar DNI real")
