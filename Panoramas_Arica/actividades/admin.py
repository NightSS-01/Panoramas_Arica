from django.contrib import admin

from .models import Actividad, Categoria, Disponibilidad, SolicitudSoporte


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


@admin.register(SolicitudSoporte)
class SolicitudSoporteAdmin(admin.ModelAdmin):
    list_display = ('creada_en', 'proveedor', 'tipo', 'estado')
    list_filter = ('estado', 'tipo')
    search_fields = ('descripcion', 'correo_contacto', 'proveedor__email')
    readonly_fields = ('proveedor', 'tipo', 'descripcion', 'correo_contacto', 'creada_en')

    def has_add_permission(self, request):
        return False