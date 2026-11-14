from django.urls import path
from . import views

app_name = 'actividades'

urlpatterns = [
    path('', views.panel_proveedor, name='panel'),
    path('crear/', views.crear_actividad, name='crear'),
    path('<int:pk>/editar/', views.editar_actividad, name='editar'),
    path('<int:pk>/publicacion/', views.alternar_publicacion, name='alternar'),
    path('<int:pk>/eliminar/', views.eliminar_actividad, name='eliminar'),
]