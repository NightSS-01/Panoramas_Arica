from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Rol, Proveedor, Administrador

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Rol', {'fields': ('rol',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Datos', {'fields': ('email', 'rol')}),)
    list_display = ('email', 'username', 'rol', 'is_active')
    
admin.site.register(Rol)
admin.site.register(Proveedor)
admin.site.register(Administrador)