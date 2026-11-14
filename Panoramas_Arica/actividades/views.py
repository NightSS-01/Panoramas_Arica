from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

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
    actividades = request.user.actividades.prefetch_related('disponibilidades')
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
    return _render_panel(request, form, abrir_modal=True)