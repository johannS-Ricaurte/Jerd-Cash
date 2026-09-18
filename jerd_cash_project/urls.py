"""
URL configuration for jerdCash project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from jerd_cash_project.apps.users.views import home_view


urlpatterns = [

    # Panel de administración
    path('admin/', admin.site.urls),

    # Página principal
    path('', home_view, name='home'),

    # URLs de usuarios
    path(
        '',
        include('jerd_cash_project.apps.users.urls')
    ),

    # URLs de préstamos
    path(
        'prestamos/',
        include('jerd_cash_project.apps.loans.urls')
    ),

    # URLs de clientes
    path(
        'cliente/',
        include('jerd_cash_project.apps.cliente.urls')
    ),

    path(
        'administrador/',
        include('jerd_cash_project.apps.administrador.urls')
    ),
]


# Archivos subidos por los usuarios
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )