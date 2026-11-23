from django.contrib import admin

from .models import Actividad, Categoria, Disponibilidad


class DisponibilidadInline(admin.TabularInline):
    model = Disponibilidad
    extra = 1


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'proveedor', 'categoria', 'modalidad', 'precio', 'publicada')
    list_filter = ('categoria', 'modalidad', 'publicada')
    inlines = [DisponibilidadInline]