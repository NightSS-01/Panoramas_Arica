from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.db.models import ProtectedError
from cuentas.decorador import rol_requerido
from .forms import ActividadForm, SolicitudSoporteForm
from django.utils import timezone


proveedor_requerido = rol_requerido('proveedor', login='cuentas:login_proveedores')

def _clp(monto):
    return '$' + f'{monto:,}'.replace(',', '.')


def _render_panel(request, form=None, form_soporte=None, abrir_modal=False, abrir_soporte=False):
    actividades = (
        request.user.actividades
        .select_related('categoria')
        .prefetch_related('disponibilidades', 'reservas__usuario')
    )
    if form is None:
        form = ActividadForm()
    if form_soporte is None:
        form_soporte = SolicitudSoporteForm(initial={'correo_contacto': request.user.email})

    # Reservas de todas las actividades de este proveedor, las más nuevas primero
    reservas = sorted(
        (r for a in actividades for r in a.reservas.all()),
        key=lambda r: r.creada_en,
        reverse=True,
    )
    exitosas = [r for r in reservas if r.exitosa]
    hoy = timezone.localdate()

    contexto = {
        'actividades': actividades,
        'total_publicadas': sum(1 for a in actividades if a.publicada),
        'reservas': reservas,
        'total_reservas': len(exitosas),
        'ingresos_texto': _clp(sum(r.monto for r in exitosas)),
        'cupos_reservados': sum(r.cantidad for r in exitosas if r.fecha >= hoy),
        'form': form,
        'form_soporte': form_soporte,
        'abrir_modal': abrir_modal,
        'abrir_soporte': abrir_soporte,
    }
    return render(request, 'actividades/panel.html', contexto)


@proveedor_requerido
def panel_proveedor(request):
    return _render_panel(request)


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
    # Reserva.actividad usa SET_NULL: la base no bloquea sola, se revisa aquí.
    # Solo cuentan las reservas vigentes; las rechazadas o anuladas no impiden borrar.
    if any(r.estado in ('pendiente', 'pagada', 'confirmada', 'sin_cupos')
           for r in actividad.reservas.all()):
        messages.error(
            request,
            f'No se puede eliminar «{titulo}» porque tiene reservas. Puedes ocultarla.',
        )
        return redirect('actividades:panel')
    actividad.delete()
    messages.success(request, f'Actividad «{titulo}» eliminada.')
    return redirect('actividades:panel')


@proveedor_requerido
@require_POST
def solicitar_soporte(request):
    form = SolicitudSoporteForm(request.POST)
    if form.is_valid():
        solicitud = form.save(commit=False)
        solicitud.proveedor = request.user
        solicitud.save()
        messages.success(request, 'Recibimos tu solicitud de soporte.')
        return redirect('actividades:panel')
    return _render_panel(request, form_soporte=form, abrir_soporte=True)