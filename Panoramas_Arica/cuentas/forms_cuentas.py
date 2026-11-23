from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, Rol, Proveedor, Consulta
from django.db import transaction

# funcion para reutilizar de clean_email
# hace que no se repita el correo
class EmailUnicoMixin:
    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError('Ya existe una cuenta con ese correo.')
        return email


class OrganizacionUnicaMixin:
    def clean_organizacion(self):
        organizacion = self.cleaned_data['organizacion'].strip()
        repetida = Proveedor.objects.filter(organizacion__iexact=organizacion)
        proveedor = getattr(self, 'proveedor', None)
        if proveedor is not None:
            repetida = repetida.exclude(pk=proveedor.pk)
        if repetida.exists():
            raise ValidationError('Ya existe un proveedor con esa organización.')
        return organizacion


class RegistroForm(EmailUnicoMixin, forms.Form):
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
            if (not usuario.check_password(password) or not usuario.is_active or usuario.rol.codigo not in self.roles_permitidos):
                raise ValidationError(self.MENSAJE)
            self.usuario = usuario
        return datos

    def get_usuario(self):
        return self.usuario

#hereda todo  de login form
class LoginProveedorForm(LoginForm):
    roles_permitidos = ('proveedor',)


#Hera todo de login form
class LoginAdministradorForm(LoginForm):
    roles_permitidos = ('administrador')

class CrearProveedorForm(EmailUnicoMixin, OrganizacionUnicaMixin, forms.Form):
    organizacion = forms.CharField(label='Organización', max_length=150)
    nombre = forms.CharField(label='Nombre del responsable', max_length=150)
    apellido = forms.CharField(label='Apellido del responsable', max_length=150)
    email = forms.EmailField(label='Correo')
    telefono = forms.CharField(label='Teléfono', max_length=20, required=False)
    password = forms.CharField(label='Contraseña inicial', widget=forms.PasswordInput)
    # aplica las reglas de contraseña de django
    def clean_password(self):
        password = self.cleaned_data['password']
        validate_password(password)
        return password

    def save(self, creado_por):
        datos = self.cleaned_data
        with transaction.atomic():
            usuario = Usuario(
                username=datos['email'], email=datos['email'],
                first_name=datos['nombre'], last_name=datos['apellido'],
                rol=Rol.objects.get(codigo='proveedor'),
            )
            usuario.set_password(datos['password'])
            usuario.save()
            return Proveedor.objects.create(
                usuario=usuario, organizacion=datos['organizacion'],
                telefono=datos['telefono'], creado_por=creado_por,
            )


class EditarProveedorForm(forms.Form):
    organizacion = forms.CharField(label='Organización', max_length=150)
    nombre = forms.CharField(label='Nombre del responsable', max_length=150)
    apellido = forms.CharField(label='Apellido del responsable', max_length=150)
    telefono = forms.CharField(label='Teléfono', max_length=20, required=False)

    def __init__(self, *args, proveedor, **kwargs):
        super().__init__(*args, **kwargs)
        self.proveedor = proveedor
        self.initial = {
            'organizacion': proveedor.organizacion,
            'nombre': proveedor.usuario.first_name,
            'apellido': proveedor.usuario.last_name,
            'telefono': proveedor.telefono,
        }

    def save(self):
        datos = self.cleaned_data
        usuario = self.proveedor.usuario
        with transaction.atomic():
            usuario.first_name = datos['nombre']
            usuario.last_name = datos['apellido']
            usuario.save()
            self.proveedor.organizacion = datos['organizacion']
            self.proveedor.telefono = datos['telefono']
            self.proveedor.save()

class ConsultaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = ['asunto', 'mensaje']


class ResponderConsultaForm(forms.ModelForm):
    respuesta = forms.CharField(label='Respuesta', widget=forms.Textarea(attrs={'rows': 5}))

    class Meta:
        model = Consulta
        fields = ['respuesta']