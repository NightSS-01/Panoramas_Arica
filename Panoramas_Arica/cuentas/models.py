from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROLES = [
        ('usuario', 'Usuario'),
        ('proveedor', 'Proveedor'),
        ('administrador', 'Administrador'),
    ]
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='usuario')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']