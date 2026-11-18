from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .forms_cuentas import RegistroForm, LoginForm

DESTINOS = {
    'usuario': 'inicio',
    'proveedor': 'actividades:panel',
    'administrador': 'index',
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
        return redirect(DESTINOS.get(request.user.rol, 'inicio'))
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            login(request, form.get_usuario())
            return redirect(DESTINOS.get(form.get_usuario().rol, 'inicio'))
    else:
        form = form_class()
    return render(request, plantilla, {'form': form})


@require_POST
def cerrar_sesion(request):
    logout(request)
    return redirect('cuentas:login')