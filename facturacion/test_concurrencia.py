"""Pruebas de bloqueo real; se omiten automáticamente fuera de PostgreSQL."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from unittest import skipUnless

from django.db import connection, connections
from django.test import TransactionTestCase

from .exceptions import MontoNotaCreditoExcedido
from .models import Cliente, Comprobante, Empresa, Producto, SerieComprobante
from .services import FacturacionService, saldo_credito


@skipUnless(
    connection.vendor == "postgresql", "Requiere PostgreSQL para verificar bloqueos de filas."
)
class ConcurrenciaTests(TransactionTestCase):
    """Usa conexiones independientes y una barrera que sincroniza solicitudes."""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            ruc="20601234567",
            razon_social="Concurrente",
            direccion="Lima",
            regimen_tributario="MYPE",
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            tipo_doc="RUC",
            num_doc="20100056781",
            razon_social="Cliente",
            direccion="Lima",
        )
        self.producto = Producto.objects.create(
            empresa=self.empresa,
            codigo="P1",
            descripcion="Producto",
            unidad_medida="NIU",
            precio_unitario="118.00",
        )
        for tipo, serie in [("F", "F001"), ("FC", "FC01")]:
            SerieComprobante.objects.create(empresa=self.empresa, tipo=tipo, serie=serie)

    def emitir(self, clave=None):
        return FacturacionService.emitir_comprobante(
            "01",
            self.empresa.pk,
            self.cliente.pk,
            [
                {
                    "producto_id": self.producto.pk,
                    "cantidad": Decimal("1.00"),
                    "precio_unitario": Decimal("118.00"),
                }
            ],
            clave_idempotencia=clave,
        )

    def ejecutar_simultaneas(self, operacion, cantidad=5):
        barrera = Barrier(cantidad)

        def ejecutar(indice):
            connections.close_all()
            try:
                barrera.wait(timeout=15)
                return operacion(indice)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=cantidad) as executor:
            return list(executor.map(ejecutar, range(cantidad)))

    def test_numeracion_sin_duplicados_ni_saltos(self):
        numeros = self.ejecutar_simultaneas(lambda indice: self.emitir().numero)
        self.assertEqual(sorted(numeros), [1, 2, 3, 4, 5])
        self.assertEqual(self.empresa.series.get(tipo="F").correlativo_actual, 5)

    def test_idempotencia_concurrente(self):
        ids = self.ejecutar_simultaneas(lambda indice: self.emitir("una-solicitud").pk)
        self.assertEqual(len(set(ids)), 1)
        self.assertEqual(Comprobante.objects.count(), 1)

    def test_creditos_concurrentes_no_superan_saldo(self):
        original = self.emitir()

        def credito(indice):
            try:
                return FacturacionService.emitir_nota_credito(
                    original.pk, "Devolución", "07", "80.00"
                ).pk
            except MontoNotaCreditoExcedido:
                return None

        resultados = self.ejecutar_simultaneas(credito, cantidad=2)
        self.assertEqual(sum(resultado is not None for resultado in resultados), 1)
        self.assertEqual(saldo_credito(original), Decimal("38.00"))
