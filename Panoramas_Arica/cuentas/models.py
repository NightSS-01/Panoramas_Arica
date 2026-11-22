from django.contrib.auth.models import AbstractUser
from django.db import models

class Rol(models.Model):
    codigo = models.SlugField(max_length=20, unique=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = 'roles'

    def __str__(self):
        return self.nombre

class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    rol = models.ForeignKey(
        Rol, on_delete=models.PROTECT,
        related_name='usuarios', to_field='codigo', default='usuario',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        self.is_staff = self.is_superuser
        super().save(*args, **kwargs)


class Proveedor(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE,
        related_name='perfil_proveedor',
        limit_choices_to={'rol__codigo': 'proveedor'},
    )
    organizacion = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20, blank=True)
    creado_por = models.ForeignKey(
        Usuario, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='proveedores_creados',
        limit_choices_to={'rol__codigo': 'administrador'},
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'proveedores'

    def __str__(self):
        return self.organizacion


class Administrador(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE,
        related_name='perfil_administrador',
        limit_choices_to={'rol__codigo': 'administrador'},
    )
    cargo = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'administradores'

    def __str__(self):
        return f'{self.usuario.email} · {self.cargo}'