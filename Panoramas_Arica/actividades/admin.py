from django.contrib import admin

from .models import Actividad, Disponibilidad


class DisponibilidadInline(admin.TabularInline):
    model = Disponibilidad
    extra = 1


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'proveedor', 'modalidad', 'precio', 'publicada')
    list_filter = ('modalidad', 'publicada')
    inlines = [DisponibilidadInline]