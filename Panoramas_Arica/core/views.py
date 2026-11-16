from django.http import Http404
from django.shortcuts import render

from .datos import ACTIVIDADES, filtrar_actividades


def inicio(request):
    actividades = filtrar_actividades(
        ACTIVIDADES,
        request.GET.get("q", ""),
        request.GET.get("modalidad", ""),
        request.GET.get("participantes", ""),
    )
    return render(request, "inicio.html", {"actividades": actividades})


def detalle(request, id):
    for actividad in ACTIVIDADES:
        if actividad["id"] == id:
            return render(request, "detalle.html", {"actividad": actividad})
    raise Http404("Actividad no encontrada")