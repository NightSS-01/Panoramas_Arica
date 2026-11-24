from django.urls import path

from . import views

app_name = 'reservas'

urlpatterns = [
    path('actividad/<int:actividad_id>/', views.iniciar, name='iniciar'),
    path('retorno/', views.retorno, name='retorno'),
    path('resultado/<int:pk>/', views.resultado, name='resultado'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
]