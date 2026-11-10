from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, RolUsuario

class LoginForm(forms.Form):
    username = forms.CharField(
        label="Usuario",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej. estudiante, docente, admin',
            'autofocus': 'autofocus'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••••'
        })
    )


class TwoFactorForm(forms.Form):
    codigo = forms.CharField(
        label="Código de verificación (6 dígitos)",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center fs-3 letter-spacing-lg',
            'placeholder': '123456',
            'autofocus': 'autofocus',
            'autocomplete': 'one-time-code',
            'pattern': '[0-9]{6}'
        })
    )


class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 10 caracteres'}),
        help_text="Dejar en blanco para mantener la contraseña actual al editar."
    )

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'rol', 'dos_factores_activo', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'dos_factores_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.instance.pk and not password:
            raise forms.ValidationError("La contraseña es obligatoria al crear un usuario.")
        if password:
            validate_password(password, self.instance)
        return password

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            usuario.set_password(password)
        if commit:
            usuario.save()
        return usuario
