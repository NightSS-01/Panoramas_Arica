from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.db.models import ProtectedError

from .forms import ActividadForm


def proveedor_requerido(vista):
    @wraps(vista)
    @login_required
    def envoltura(request, *args, **kwargs):
        if request.user.rol != 'proveedor':
            raise PermissionDenied
        return vista(request, *args, **kwargs)
    return envoltura


def _render_panel(request, form, abrir_modal=False):
    actividades = (
        request.user.actividades
        .select_related('categoria')
        .prefetch_related('disponibilidades')
    )
    contexto = {
        'actividades': actividades,
        'total_publicadas': sum(1 for a in actividades if a.publicada),
        'form': form,
        'abrir_modal': abrir_modal,
    }
    return render(request, 'actividades/panel.html', contexto)


@proveedor_requerido
def panel_proveedor(request):
    return _render_panel(request, ActividadForm())


@proveedor_requerido
@require_POST
def crear_actividad(request):
    form = ActividadForm(request.POST, request.FILES)
    if form.is_valid():
        actividad = form.guardar(request.user)
        messages.success(request, f'Actividad «{actividad.titulo}» creada.')
        return redirect('actividades:panel')
    return _render_panel(request, form=form, abrir_modal=True)

@proveedor_requerido
def editar_actividad(request, pk):
    actividad = get_object_or_404(request.user.actividades, pk=pk)
    if request.method == 'POST':
        form = ActividadForm(request.POST, request.FILES, instance=actividad)
        if form.is_valid():
            form.guardar(request.user)
            messages.success(request, 'Los cambios se guardaron.')
            return redirect('actividades:panel')
    else:
        form = ActividadForm(instance=actividad)
    return render(request, 'actividades/editar.html', {'form': form, 'actividad': actividad})


@proveedor_requerido
@require_POST
def alternar_publicacion(request, pk):
    actividad = get_object_or_404(request.user.actividades, pk=pk)
    actividad.publicada = not actividad.publicada
    actividad.save(update_fields=['publicada'])
    estado = 'publicada' if actividad.publicada else 'oculta'
    messages.success(request, f'«{actividad.titulo}» ahora está {estado}.')
    return redirect('actividades:panel')

@proveedor_requerido
@require_POST
def eliminar_actividad(request, pk):
    actividad = get_object_or_404(request.user.actividades, pk=pk)
    titulo = actividad.titulo
    try:
        actividad.delete()
    except ProtectedError:
        messages.error(
            request,
            f'No se puede eliminar {titulo} porque tiene reservas. Puedes ocultarla.',
        )
    else:
        messages.success(request, f'Actividad {titulo} eliminada.')
    return redirect('actividades:panel')