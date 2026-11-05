"""Defensa de documentos históricos incluso frente al borrado por queryset."""

from django.core.exceptions import ValidationError
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from .models import Comprobante, DetalleComprobante


@receiver(pre_delete, sender=Comprobante)
def proteger_documento(sender, instance, **kwargs):
    """Rechaza el borrado de cualquier comprobante numerado."""
    if instance.estado != "BORRADOR":
        raise ValidationError("Los documentos emitidos no se pueden eliminar.")


@receiver(pre_save, sender=Comprobante)
def proteger_importes(sender, instance, **kwargs):
    """Impide editar datos históricos tras emitir; los estados usan servicios."""
    if not instance.pk:
        return
    anterior = sender.objects.filter(pk=instance.pk).first()
    if anterior and anterior.estado != instance.estado:
        from .services import TRANSICIONES

        if instance.estado not in TRANSICIONES[anterior.estado]:
            raise ValidationError("Transición de estado no permitida.")
    if anterior and anterior.estado != "BORRADOR":
        campos = [
            "empresa_id",
            "cliente_id",
            "tipo",
            "serie",
            "numero",
            "subtotal",
            "igv",
            "total",
            "datos_historicos",
            "fecha",
            "creado_por_id",
            "clave_idempotencia",
        ]
        if any(getattr(anterior, campo) != getattr(instance, campo) for campo in campos):
            raise ValidationError("El contenido de un documento emitido es inmutable.")


@receiver(pre_delete, sender=DetalleComprobante)
@receiver(pre_save, sender=DetalleComprobante)
def proteger_detalle(sender, instance, **kwargs):
    """Conserva cantidades y precios originales de documentos emitidos."""
    if instance.comprobante.estado != "BORRADOR":
        raise ValidationError("No se pueden modificar líneas de documentos emitidos.")
