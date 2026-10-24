"""
URL configuration for JERD-Cash.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from jerd_cash_project.apps.users.views import home_view


urlpatterns = [

    # Administración interna de Django
    path(
        'gestion-interna/',
        admin.site.urls
    ),

    # Página principal
    path(
        '',
        home_view,
        name='home'
    ),

    # Usuarios
    path(
        '',
        include('jerd_cash_project.apps.users.urls')
    ),

    # Préstamos
    path(
        'servicios/',
        include('jerd_cash_project.apps.loans.urls')
    ),

    # Clientes
    path(
        'cuenta/',
        include('jerd_cash_project.apps.cliente.urls')
    ),

    # Administración de JERD-Cash
    path(
        'panel/',
        include('jerd_cash_project.apps.administrador.urls')
    ),
]


# Archivos subidos por los usuarios
if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )