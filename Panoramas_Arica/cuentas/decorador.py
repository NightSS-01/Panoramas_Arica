from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def rol_requerido(*roles, login='cuentas:login'):
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(login)
            if request.user.rol not in roles:
                raise PermissionDenied
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador