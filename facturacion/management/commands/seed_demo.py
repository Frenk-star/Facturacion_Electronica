"""Carga de demostración repetible sin credenciales permanentes."""

import os
import secrets
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from facturacion.models import Cliente, Empresa, Membresia, Producto, SerieComprobante
from facturacion.services import FacturacionService


class Command(BaseCommand):
    help = "Crea empresa, roles, usuarios y documentos académicos sin duplicaciones."

    @transaction.atomic
    def handle(self, *args, **options):
        empresa, _ = Empresa.objects.get_or_create(
            ruc="20601234567",
            defaults={
                "razon_social": "COMERCIALIZADORA DEL NORTE S.A.C.",
                "nombre_comercial": "Comercial Norte",
                "direccion": "Av. Balta 1234, Chiclayo, Lambayeque",
                "regimen_tributario": "MYPE",
            },
        )
        usuarios = {}
        for rol, _ in Membresia.ROLES:
            grupo, _ = Group.objects.get_or_create(name=rol)
            usuario, nuevo = get_user_model().objects.get_or_create(username=f"demo_{rol.lower()}")
            if nuevo:
                password = os.getenv("DEMO_PASSWORD") or secrets.token_urlsafe(18)
                usuario.set_password(password)
                usuario.save()
                self.stdout.write(f"Usuario: {usuario.username} | Contraseña inicial: {password}")
            usuario.groups.add(grupo)
            Membresia.objects.get_or_create(usuario=usuario, empresa=empresa, defaults={"rol": rol})
            usuarios[rol] = usuario
        for tipo, serie in [("F", "F001"), ("B", "B001"), ("FC", "FC01")]:
            SerieComprobante.objects.get_or_create(empresa=empresa, tipo=tipo, serie=serie)
        cliente, _ = Cliente.objects.get_or_create(
            empresa=empresa,
            tipo_doc="RUC",
            num_doc="20100056781",
            defaults={
                "razon_social": "DISTRIBUIDORA FERRETERA PERÚ E.I.R.L.",
                "direccion": "Av. Grau 456, Chiclayo",
                "email": "ventas@example.com",
            },
        )
        consumidor, _ = Cliente.objects.get_or_create(
            empresa=empresa,
            tipo_doc="DNI",
            num_doc="45891234",
            defaults={
                "razon_social": "JUAN CARLOS PÉREZ GÓMEZ",
                "direccion": "Calle Los Laureles 789, Lambayeque",
            },
        )
        productos = []
        for codigo, descripcion, precio, afecto in [
            ("PROD-001", "Cemento Sol tipo I · Bolsa 42.5 kg", "28.50", True),
            ("PROD-002", "Fierro corrugado 1/2 pulgada x 9 m", "42.00", True),
            ("SERV-001", "Servicio de transporte de carga local", "150.00", True),
            ("PROD-003", "Producto de demostración no gravado", "35.00", False),
        ]:
            producto, _ = Producto.objects.get_or_create(
                empresa=empresa,
                codigo=codigo,
                defaults={
                    "descripcion": descripcion,
                    "unidad_medida": "NIU",
                    "precio_unitario": Decimal(precio),
                    "afecto_igv": afecto,
                },
            )
            productos.append(producto)
        original = None
        for indice, (tipo, receptor, resultado) in enumerate(
            [
                ("01", cliente, "ACEPTADO"),
                ("03", consumidor, "ACEPTADO"),
                ("01", cliente, "RECHAZADO"),
            ]
        ):
            documento = FacturacionService.emitir_comprobante(
                tipo,
                empresa.pk,
                receptor.pk,
                [
                    {
                        "producto": productos[indice],
                        "cantidad": Decimal("2.00"),
                        "precio_unitario": productos[indice].precio_unitario,
                    }
                ],
                usuario=usuarios["EMISOR"],
                resultado_mock=resultado,
                clave_idempotencia=f"demo-documento-{indice}",
            )
            if indice == 0:
                original = documento
        FacturacionService.emitir_nota_credito(
            original.pk,
            "Devolución parcial de demostración",
            "07",
            "11.80",
            usuario=usuarios["EMISOR"],
            clave_idempotencia="demo-credito-1",
        )
        FacturacionService.emitir_comprobante(
            "03",
            empresa.pk,
            consumidor.pk,
            [
                {
                    "producto": productos[3],
                    "cantidad": Decimal("1.00"),
                    "precio_unitario": productos[3].precio_unitario,
                }
            ],
            usuario=usuarios["EMISOR"],
            borrador=True,
            clave_idempotencia="demo-borrador-1",
        )
        self.stdout.write(
            self.style.SUCCESS("Demostración creada. OSE simulado, sin validez tributaria.")
        )
