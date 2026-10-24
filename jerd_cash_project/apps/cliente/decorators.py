from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def cliente_required(view_func):

    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if getattr(request.user, 'role', None) != 'cliente':
            raise PermissionDenied(
                'No tienes permisos para acceder a esta sección.'
            )

        return view_func(request, *args, **kwargs)

    return wrapper