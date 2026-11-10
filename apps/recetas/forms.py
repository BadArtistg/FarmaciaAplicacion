from django import forms
from django.utils import timezone
from .models import Receta, ItemReceta, Paciente
from apps.inventario.models import Producto


class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['paciente', 'medico', 'fecha', 'observaciones']
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-select'}),
            'medico': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Dr. Andrés Soto'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Indicaciones clínicas o diagnóstico...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('fecha'):
            self.initial['fecha'] = timezone.localdate()


class ItemRecetaForm(forms.ModelForm):
    class Meta:
        model = ItemReceta
        fields = ['producto', 'cantidad_prescrita', 'modalidad']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_prescrita': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
            'modalidad': forms.Select(attrs={'class': 'form-select'}),
        }
