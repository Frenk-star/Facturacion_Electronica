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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tipo = self.data.get("tipo_doc") if self.is_bound else self.instance.tipo_doc
        self.fields["razon_social"].label = (
            "Razón social" if tipo in {"", "RUC"} else "Nombres y apellidos"
        )

    class Meta:
        model = Cliente
        fields = ["tipo_doc", "num_doc", "razon_social", "direccion", "email", "activo"]
        labels = {
            "tipo_doc": "Tipo de documento",
            "num_doc": "Número de documento",
            "direccion": "Dirección",
            "email": "Correo electrónico",
            "activo": "Cliente activo",
        }
        help_texts = {
            "num_doc": "DNI: 8 dígitos. RUC: 11 dígitos.",
            "razon_social": "Revisa el nombre obtenido o complétalo manualmente.",
            "direccion": "Completa la dirección del cliente; la consulta DNI solo obtiene el nombre.",
            "email": "Opcional. Se completa manualmente.",
        }


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
