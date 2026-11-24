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
    path('panel/', views.panel_admin, name='panel_admin'),
    path('panel/proveedores/', views.panel_proveedores, name='panel_proveedores'),
    path('panel/proveedores/<int:pk>/editar/', views.panel_proveedor_editar, name='panel_proveedor_editar'),
    path('panel/proveedores/<int:pk>/estado/', views.panel_proveedor_estado, name='panel_proveedor_estado'),
    path('panel/proveedores/<int:pk>/', views.panel_proveedor_detalle, name='panel_proveedor_detalle'),
    path('consulta/enviar/', views.consulta_enviar, name='consulta_enviar'),
    path('panel/consultas/', views.panel_consultas, name='panel_consultas'),
    path('panel/consultas/<int:pk>/', views.panel_consulta_detalle, name='panel_consulta_detalle'),
    path('panel/reservas/', views.panel_reservas, name='panel_reservas'),
]