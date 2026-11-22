from django.contrib.auth import login, logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
# Q del ORM de Django para crear consultas complejas en la base de datos usando operadores lógicos (OR, AND y NOT)
# Los argumentos normales en .filter() siempre se combinan con un AND. Con Q puedes escribir condiciones más flexibles
from django.db.models import Q
from .decorador import rol_requerido
from .forms_cuentas import RegistroForm, LoginForm, CrearProveedorForm, EditarProveedorForm
from .models import Proveedor
DESTINOS = {
    'usuario': 'inicio',
    'proveedor': 'actividades:panel',
    'administrador': 'cuentas:panel_admin',
}

def registro(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cuentas:login')
    else:
        form = RegistroForm()
    return render(request, 'cuentas/registro.html', {'form': form})


def ingreso(request, form_class=LoginForm, plantilla='cuentas/login.html'):
    if request.user.is_authenticated:
        return redirect(DESTINOS.get(request.user.rol.codigo, 'inicio'))
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            login(request, form.get_usuario())
            return redirect(DESTINOS.get(form.get_usuario().rol.codigo, 'inicio'))
    else:
        form = form_class()
    return render(request, plantilla, {'form': form})


@require_POST
def cerrar_sesion(request):
    logout(request)
    return redirect('cuentas:login')

@rol_requerido('administrador', login='cuentas:login_administradores')
def panel_admin(request):
    return render(request, 'panel_administrador/resumen.html')

@rol_requerido('administrador', login='cuentas:login_administradores')
def panel_proveedores(request):
    form = CrearProveedorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save(creado_por=request.user)
        messages.success(request, 'Proveedor creado correctamente.')
        return redirect('cuentas:panel_proveedores')
    q = request.GET.get('q', '').strip()
    proveedores = Proveedor.objects.select_related('usuario', 'creado_por').order_by('organizacion')
    if q:
        proveedores = proveedores.filter(
            Q(organizacion__icontains=q)
            | Q(usuario__first_name__icontains=q)
            | Q(usuario__last_name__icontains=q)
            | Q(usuario__email__icontains=q)
        )
    return render(request, 'panel_administrador/proveedores.html',
                  {'proveedores': proveedores, 'q': q, 'form': form, 'abrir_modal': request.method == 'POST'})

@rol_requerido('administrador', login='cuentas:login_administradores')
def panel_proveedor_editar(request, pk):
    proveedor = get_object_or_404(Proveedor.objects.select_related('usuario'), pk=pk)
    form = EditarProveedorForm(request.POST or None, proveedor=proveedor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Proveedor actualizado correctamente.')
        return redirect('cuentas:panel_proveedores')
    return render(request, 'panel_administrador/proveedores_editar.html',
                  {'form': form, 'proveedor': proveedor})

@rol_requerido('administrador', login='cuentas:login_administradores')
@require_POST
def panel_proveedor_estado(request, pk):
    proveedor = get_object_or_404(Proveedor.objects.select_related('usuario'), pk=pk)
    usuario = proveedor.usuario
    usuario.is_active = not usuario.is_active
    usuario.save()
    estado = 'reactivada' if usuario.is_active else 'desactivada'
    messages.success(request, f'Cuenta de {proveedor.organizacion} {estado}.')
    return redirect('cuentas:panel_proveedor_editar', pk=proveedor.pk)

@rol_requerido('administrador', login='cuentas:login_administradores')
def panel_proveedor_detalle(request, pk):
    proveedor = get_object_or_404(
        Proveedor.objects.select_related('usuario', 'creado_por'), pk=pk
    )
    actividades = proveedor.usuario.actividades.prefetch_related('disponibilidades')
    return render(request, 'panel_administrador/proveedores_detalles.html',
                  {'proveedor': proveedor, 'actividades': actividades})