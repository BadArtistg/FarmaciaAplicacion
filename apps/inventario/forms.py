from django import forms
from django.utils import timezone
from .models import Producto, Lote


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'codigo',
            'nombre',
            'forma_farmaceutica',
            'dosis',
            'condicion_venta',
            'es_controlado',
            'precio',
            'stock_minimo'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. MED-PAR-500'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Paracetamol'}),
            'forma_farmaceutica': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Comprimidos'}),
            'dosis': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 500 mg'}),
            'condicion_venta': forms.Select(attrs={'class': 'form-select'}),
            'es_controlado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['producto', 'codigo', 'fecha_vencimiento', 'cantidad_inicial']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. PA-2201'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cantidad_inicial': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': '100'}),
        }

    def clean_fecha_vencimiento(self):
        fecha = self.cleaned_data.get('fecha_vencimiento')
        if fecha:
            hoy = timezone.localdate()
            if fecha <= hoy:
                raise forms.ValidationError(
                    f'Fecha inválida: el lote no puede estar vencido ({fecha}). Debe ser posterior a hoy ({hoy}).'
                )
        return fecha

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        codigo = cleaned_data.get('codigo')

        if producto and codigo:
            # Validar unicidad (producto, codigo) para mensaje amigable
            qs = Lote.objects.filter(producto=producto, codigo=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('codigo', f"Ya existe un lote con el código '{codigo}' para el producto '{producto.nombre}'.")

        return cleaned_data
