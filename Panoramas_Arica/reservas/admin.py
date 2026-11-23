from django.contrib import admin

from .models import Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('buy_order', 'actividad_titulo', 'usuario', 'cantidad', 'monto', 'estado', 'creada_en')
    list_filter = ('estado',)
    search_fields = ('buy_order', 'actividad_titulo', 'usuario__email')