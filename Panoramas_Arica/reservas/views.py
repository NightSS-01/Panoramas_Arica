import uuid

import requests
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from transbank.error.transbank_error import TransbankError

from django.db.models import Q
from django.utils import timezone

from actividades.models import Actividad, Disponibilidad
from cuentas.decorador import rol_requerido

from . import transbank
from .forms import ReservaForm
from .models import Reserva

ERRORES_DE_RED = (TransbankError, requests.RequestException)


def _motivo_bloqueo(actividad):
    if actividad.modalidad == Actividad.Modalidad.DIFUSION:
        return 'Esta actividad es de difusión y no admite reservas.'
    if actividad.precio is None:
        return 'El precio de esta actividad aún no está confirmado.'
    return ''


def _nueva_orden():
    return 'PA' + uuid.uuid4().hex[:20]


def _crear_reserva(request, actividad, disponibilidad, cantidad, estado):
    return Reserva.objects.create(
        usuario=request.user,
        actividad=actividad,
        disponibilidad=disponibilidad,
        actividad_titulo=actividad.titulo,
        fecha=disponibilidad.fecha,
        cantidad=cantidad,
        monto=actividad.precio * cantidad,
        estado=estado,
        buy_order=_nueva_orden(),
    )


@rol_requerido('usuario')
def iniciar(request, actividad_id):
    actividad = get_object_or_404(Actividad, pk=actividad_id, publicada=True)
    form = ReservaForm(request.POST or None, actividad=actividad)

    motivo = _motivo_bloqueo(actividad)
    if not motivo and not form.fields['disponibilidad'].queryset.exists():
        motivo = 'Esta actividad no tiene fechas con cupos disponibles.'

    if not motivo and request.method == 'POST' and form.is_valid():
        disponibilidad = form.cleaned_data['disponibilidad']
        cantidad = form.cleaned_data['cantidad']
        if actividad.precio * cantidad == 0:
            reserva = _reservar_sin_costo(request, actividad, disponibilidad, cantidad)
            if reserva:
                return redirect('reservas:resultado', pk=reserva.pk)
            form.add_error('cantidad', 'Ya no quedan cupos suficientes para esa fecha.')
        else:
            return _iniciar_pago(request, actividad, disponibilidad, cantidad)

    return render(request, 'reservas/iniciar.html',
                  {'actividad': actividad, 'form': form, 'motivo': motivo})


def _reservar_sin_costo(request, actividad, disponibilidad, cantidad):
    """Reserva directa, sin pasar por Transbank. Devuelve None si ya no hay cupos."""
    with transaction.atomic():
        disp = Disponibilidad.objects.select_for_update().get(pk=disponibilidad.pk)
        if disp.cupos < cantidad:
            return None
        disp.cupos -= cantidad
        disp.save(update_fields=['cupos'])
        return _crear_reserva(request, actividad, disp, cantidad, Reserva.Estado.CONFIRMADA)


def _iniciar_pago(request, actividad, disponibilidad, cantidad):
    reserva = _crear_reserva(request, actividad, disponibilidad, cantidad, Reserva.Estado.PENDIENTE)
    return_url = request.build_absolute_uri(reverse('reservas:retorno'))
    try:
        respuesta = transbank.crear(
            reserva.buy_order, f'usuario-{request.user.pk}', reserva.monto, return_url
        )
    except ERRORES_DE_RED:
        reserva.estado = Reserva.Estado.RECHAZADA
        reserva.save(update_fields=['estado', 'actualizada_en'])
        return redirect('reservas:resultado', pk=reserva.pk)

    reserva.token = respuesta['token']
    reserva.save(update_fields=['token', 'actualizada_en'])
    return render(request, 'reservas/redireccion.html',
                  {'url': respuesta['url'], 'token': respuesta['token']})


@csrf_exempt  # Transbank vuelve a este sitio con un POST que no trae token CSRF
def retorno(request):
    datos = {**request.GET.dict(), **request.POST.dict()}
    token_ws = datos.get('token_ws', '')
    tbk_token = datos.get('TBK_TOKEN', '')
    orden = datos.get('TBK_ORDEN_COMPRA', '')

    if token_ws and not tbk_token:
        # Camino normal: el cliente pagó (o intentó pagar) en Webpay
        reserva = get_object_or_404(Reserva, token=token_ws)
        _confirmar_pago(reserva)
    elif tbk_token or orden:
        # El cliente anuló el pago, o se acabó el tiempo del formulario
        reserva = None
        if tbk_token:
            reserva = Reserva.objects.filter(token=tbk_token).first()
        if reserva is None and orden:
            reserva = Reserva.objects.filter(buy_order=orden).first()
        if reserva is None:
            raise Http404
        if reserva.estado == Reserva.Estado.PENDIENTE:
            reserva.estado = Reserva.Estado.ANULADA
            reserva.save(update_fields=['estado', 'actualizada_en'])
    else:
        return redirect('inicio')

    return redirect('reservas:resultado', pk=reserva.pk)


def _confirmar_pago(reserva):
    if reserva.estado != Reserva.Estado.PENDIENTE:
        return  # ya se procesó (por ejemplo, el cliente recargó la página)

    try:
        respuesta = transbank.confirmar(reserva.token)
    except ERRORES_DE_RED:
        reserva.refresh_from_db()
        if reserva.estado == Reserva.Estado.PENDIENTE:
            reserva.estado = Reserva.Estado.RECHAZADA
            reserva.save(update_fields=['estado', 'actualizada_en'])
        return

    aprobado = (
        respuesta.get('status') == 'AUTHORIZED'
        and respuesta.get('response_code') == 0
        and respuesta.get('amount') == reserva.monto  # el monto debe coincidir con el nuestro
    )

    with transaction.atomic():
        reserva = Reserva.objects.select_for_update().get(pk=reserva.pk)
        if reserva.estado != Reserva.Estado.PENDIENTE:
            return
        reserva.codigo_autorizacion = respuesta.get('authorization_code') or ''
        if not aprobado:
            reserva.estado = Reserva.Estado.RECHAZADA
        else:
            disp = None
            if reserva.disponibilidad_id:
                disp = Disponibilidad.objects.select_for_update().get(pk=reserva.disponibilidad_id)
            if disp and disp.cupos >= reserva.cantidad:
                disp.cupos -= reserva.cantidad
                disp.save(update_fields=['cupos'])
                reserva.estado = Reserva.Estado.PAGADA
            else:
                reserva.estado = Reserva.Estado.SIN_CUPOS
        reserva.save()


@rol_requerido('usuario')
def resultado(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, usuario=request.user)
    return render(request, 'reservas/resultado.html', {'reserva': reserva})

@rol_requerido('usuario')
def mis_reservas(request):
    pestana = 'historial' if request.GET.get('pestana') == 'historial' else 'proximas'
    hoy = timezone.localdate()
    vigentes = Q(
        estado__in=[Reserva.Estado.PENDIENTE, Reserva.Estado.PAGADA,
                    Reserva.Estado.CONFIRMADA, Reserva.Estado.SIN_CUPOS],
        fecha__gte=hoy,
    )
    propias = Reserva.objects.filter(usuario=request.user).select_related(
        'actividad__proveedor__perfil_proveedor'
    )
    proximas = propias.filter(vigentes).order_by('fecha')
    historial = propias.exclude(vigentes)
    return render(request, 'reservas/mis_reservas.html', {
        'pestana': pestana,
        'reservas': proximas if pestana == 'proximas' else historial,
        'total_proximas': proximas.count(),
        'total_historial': historial.count(),
    })