from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Usuario


class RegistroForm(forms.Form):
    nombre = forms.CharField(
        label='Nombre',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'name'}),
    )
    email = forms.EmailField(
        label='Correo',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
    )
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError('Ya existe una cuenta con ese correo.')
        return email

    def clean(self):
        datos = super().clean()
        p1 = datos.get('password1')
        p2 = datos.get('password2')
        if p1 and p2:
            if p1 != p2:
                self.add_error('password2', 'Las contraseñas no coinciden.')
            else:
                try:
                    validate_password(p1)
                except ValidationError as error:
                    self.add_error('password1', error)
        return datos

    def save(self):
        usuario = Usuario(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['nombre'],
        )
        usuario.set_password(self.cleaned_data['password1'])
        usuario.save()
        return usuario


class LoginForm(forms.Form):
    MENSAJE = 'Correo o contraseña incorrectos.'
    roles_permitidos = ('usuario',)
    email = forms.EmailField(
        label='Correo',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )
    usuario = None

    def clean(self):
        datos = super().clean()
        email = datos.get('email')
        password = datos.get('password')
        if email and password:
            usuario = Usuario.objects.filter(email__iexact=email.strip()).first()
            if usuario is None:
                Usuario().set_password(password)
                raise ValidationError(self.MENSAJE)
            if (not usuario.check_password(password) or not usuario.is_active or usuario.rol not in self.roles_permitidos):
                raise ValidationError(self.MENSAJE)
            self.usuario = usuario
        return datos

    def get_usuario(self):
        return self.usuario

#hereda todo  de login form
class LoginProveedorForm(LoginForm):
    roles_permitidos = ('proveedor',)