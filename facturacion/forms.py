"""Formularios web con las mismas validaciones del modelo que la API."""

from django import forms

from .models import Cliente, Producto


class EstiloFormularioMixin:
    """Aplica controles Bootstrap sin duplicar plantillas de campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs["class"] = (
                "form-check-input"
                if isinstance(campo.widget, forms.CheckboxInput)
                else "form-control"
            )
            if isinstance(campo.widget, forms.Textarea):
                campo.widget.attrs["rows"] = 3


class ClienteForm(EstiloFormularioMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["tipo_doc", "num_doc", "razon_social", "direccion", "email", "activo"]


class ProductoForm(EstiloFormularioMixin, forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "codigo",
            "descripcion",
            "unidad_medida",
            "precio_unitario",
            "afecto_igv",
            "activo",
        ]
