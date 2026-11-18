from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from actividades.models import Actividad


def inicio(request):
    q = request.GET.get("q", "").strip()
    modalidad = request.GET.get("modalidad", "")
    participantes = request.GET.get("participantes", "")

    actividades = Actividad.objects.filter(publicada=True).prefetch_related("disponibilidades")

    if q:
        actividades = actividades.filter(
            Q(titulo__icontains=q)
            | Q(descripcion__icontains=q)
            | Q(ubicacion__icontains=q)
        )

    if modalidad:
        actividades = actividades.filter(modalidad=modalidad)

    if participantes.isdigit():
        actividades = actividades.filter(
            disponibilidades__cupos__gte=int(participantes)
        ).distinct()

    return render(request, "inicio.html", {"actividades": actividades})


def detalle(request, id):
    actividad = get_object_or_404(Actividad, pk=id, publicada=True)
    return render(request, "detalle.html", {"actividad": actividad})