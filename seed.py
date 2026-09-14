import os
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FacturacionSunat.settings')
django.setup()

from decimal import Decimal
from facturacion.models import Empresa, SerieComprobante, Cliente, Producto


def run_seeder():
    print("Iniciando carga de datos de prueba (Seeder)...")

    # 1. Crear Empresa
    empresa, created = Empresa.objects.get_or_create(
        ruc="20601234567",
        defaults={
            "razon_social": "COMERCIALIZADORA DEL NORTE S.A.C.",
            "nombre_comercial": "COMERCIAL NORTE",
            "direccion": "Av. Balta 1234, Chiclayo, Lambayeque",
            "regimen_tributario": "MYPE"
        }
    )
    if created:
        print(f"✓ Empresa creada: {empresa.razon_social}")
    else:
        print(f"• Empresa ya existente: {empresa.razon_social}")

    # 2. Crear Series de Comprobantes (Factura, Boleta y Nota de Crédito)
    series_data = [
        ('F', 'F001'),
        ('B', 'B001'),
        ('FC', 'FC01'),
    ]

    for tipo, serie in series_data:
        s_obj, s_created = SerieComprobante.objects.get_or_create(
            empresa=empresa,
            tipo=tipo,
            serie=serie,
            defaults={"correlativo_actual": 0}
        )
        if s_created:
            print(f"✓ Serie creada: {serie} ({tipo})")

    # 3. Crear Clientes
    clientes_data = [
        {
            "tipo_doc": "RUC",
            "num_doc": "20100056781",
            "razon_social": "DISTRIBUIDORA FERRETERA PERU E.I.R.L.",
            "direccion": "Av. Grau 456, Chiclayo",
            "email": "ventas@distribuidora.pe"
        },
        {
            "tipo_doc": "DNI",
            "num_doc": "45891234",
            "razon_social": "JUAN CARLOS PEREZ GOMEZ",
            "direccion": "Calle Los Laureles 789, Lambayeque",
            "email": "juan.perez@gmail.com"
        }
    ]

    for c in clientes_data:
        cli_obj, cli_created = Cliente.objects.get_or_create(
            num_doc=c["num_doc"],
            defaults=c
        )
        if cli_created:
            print(f"✓ Cliente creado: {cli_obj.razon_social}")

    # 4. Crear Productos / Servicios
    productos_data = [
        {
            "codigo": "PROD-001",
            "descripcion": "CEMENTO SOL TIPO I (BOLSA 42.5 KG)",
            "unidad_medida": "NIU",
            "precio_unitario": Decimal("28.50"),
            "afecto_igv": True
        },
        {
            "codigo": "PROD-002",
            "descripcion": "FIERRO CORRUGADO 1/2 PULGADA x 9M",
            "unidad_medida": "NIU",
            "precio_unitario": Decimal("42.00"),
            "afecto_igv": True
        },
        {
            "codigo": "SERV-001",
            "descripcion": "SERVICIO DE TRANSPORTE DE CARGA LOCAL",
            "unidad_medida": "ZZ",
            "precio_unitario": Decimal("150.00"),
            "afecto_igv": True
        }
    ]

    for p in productos_data:
        prod_obj, prod_created = Producto.objects.get_or_create(
            codigo=p["codigo"],
            defaults=p
        )
        if prod_created:
            print(f"✓ Producto creado: {prod_obj.descripcion}")

    print("\n¡Poblamiento de datos completado con éxito!")


if __name__ == '__main__':
    run_seeder()