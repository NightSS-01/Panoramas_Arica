from django.urls import path
from . import views
from .forms_cuentas import LoginProveedorForm, LoginAdministradorForm

app_name = 'cuentas'

urlpatterns = [
     path('login/', views.ingreso, name='login'),
     path('registro/', views.registro, name='registro'),
     path('logout/', views.cerrar_sesion, name='salir'),
     path('proveedores/login/', views.ingreso,
         {'form_class': LoginProveedorForm, 'plantilla': 'cuentas/login_proveedores.html'},
         name='login_proveedores'),
     path('administradores/login/', views.ingreso,
     {'form_class': LoginAdministradorForm, 'plantilla': 'cuentas/login_administradores.html'},
     name='login_administradores'),
]