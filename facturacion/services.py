from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import SerieComprobante, Comprobante, DetalleComprobante, LogEnvioSUNAT, NotaCredito, Empresa

class FacturacionService:

    @staticmethod
    @transaction.atomic
    def emitir_comprobante(tipo_comp, empresa_id, cliente_id, items_data):
        """
        Emite comprobantes con precios que incluyen IGV, aplicando el desglose:
        $$\\text{Base} = \\frac{\\text{Monto Total}}{1.18}$$
        $$\\text{IGV} = \\text{Monto Total} - \\text{Base}$$
        """
        tipo_serie = 'F' if tipo_comp == '01' else 'B'
        
        empresa = Empresa.objects.get(id=empresa_id)
        
        serie_obj = SerieComprobante.objects.select_for_update().get(
            empresa_id=empresa_id, tipo=tipo_serie
        )
        serie_obj.correlativo_actual += 1
        serie_obj.save()
        
        nuevo_numero = serie_obj.correlativo_actual

        subtotal_general = Decimal('0.00')
        igv_general = Decimal('0.00')
        
        comprobante = Comprobante(
            empresa=empresa,
            serie=serie_obj.serie,
            numero=nuevo_numero,
            cliente_id=cliente_id,
            tipo=tipo_comp,
            subtotal=0,
            igv=0,
            total=0,
            estado='BORRADOR'
        )
        # Ejecutar validaciones del modelo (como la restricción de RUC)
        comprobante.clean()
        comprobante.save()

        for item in items_data:
            producto = item['producto']
            cantidad = Decimal(str(item['cantidad']))
            precio_unitario_con_igv = Decimal(str(item['precio_unitario']))
            descuento = Decimal(str(item.get('descuento', '0.00')))

            # Monto total de la línea incluyendo IGV menos descuento
            total_linea = (cantidad * precio_unitario_con_igv) - descuento

            if producto.afecto_igv:
                # Desglose de precios que ya incluyen IGV
                base_linea = (total_linea / Decimal('1.18')).quantize(Decimal('0.01'))
                igv_linea = (total_linea - base_linea).quantize(Decimal('0.01'))
            else:
                base_linea = total_linea
                igv_linea = Decimal('0.00')

            subtotal_general += base_linea
            igv_general += igv_linea

            DetalleComprobante.objects.create(
                comprobante=comprobante,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario_con_igv,
                descuento=descuento,
                igv_linea=igv_linea,
                subtotal=base_linea
            )

        comprobante.subtotal = subtotal_general
        comprobante.igv = igv_general
        comprobante.total = subtotal_general + igv_general
        comprobante.estado = 'EMITIDO'
        comprobante.save()

        FacturacionService.enviar_a_sunat(comprobante)

        return comprobante

    @staticmethod
    def enviar_a_sunat(comprobante):
        comprobante.estado = 'ENVIADO'
        comprobante.xml_firmado = f"<?xmlversion='1.0'?><Invoice><ID>{comprobante.serie}-{comprobante.numero}</ID><Total>{comprobante.total}</Total></Invoice>"
        comprobante.save()

        codigo = "0"
        descripcion = f"El comprobante {comprobante.serie}-{comprobante.numero} ha sido aceptado exitosamente."
        estado_resp = "ACEPTADO"

        comprobante.estado = estado_resp
        comprobante.save()

        LogEnvioSUNAT.objects.create(
            comprobante=comprobante,
            estado_respuesta=estado_resp,
            codigo_respuesta=codigo,
            descripcion=descripcion
        )

    @staticmethod
    @transaction.atomic
    def emitir_nota_credito(comprobante_original_id, motivo, tipo_nota, monto_afectado):
        """Emite una Nota de Crédito validando estado ACEPTADO y límite de monto."""
        original = Comprobante.objects.select_for_update().get(id=comprobante_original_id)
        
        if original.estado != 'ACEPTADO':
            raise ValidationError("Solo se pueden emitir notas de crédito sobre comprobantes en estado ACEPTADO.")
        
        monto_dec = Decimal(str(monto_afectado))
        if monto_dec > original.total:
            raise ValidationError("El monto de la nota de crédito no puede superar el total del comprobante original.")

        nc = NotaCredito.objects.create(
            comprobante_referencia=original,
            motivo=motivo,
            tipo_nota=tipo_nota,
            monto_afectado=monto_dec
        )
        return nc