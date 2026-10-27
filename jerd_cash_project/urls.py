
"""
URL configuration for JERD-Cash.
"""

from pathlib import Path

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse
from django.views.generic import TemplateView

from jerd_cash_project.apps.users.views import home_view


# ==========================================
# SERVICE WORKER DE LA PWA
# ==========================================

def service_worker_view(request):

    archivo = Path(settings.BASE_DIR) / 'pwa' / 'service-worker.js'

    respuesta = FileResponse(
        open(archivo, 'rb'),
        content_type='text/javascript'
    )

    # Evitar que el navegador conserve versiones antiguas
    respuesta['Cache-Control'] = 'no-cache'

    # Permitir que controle las rutas de la aplicación
    respuesta['Service-Worker-Allowed'] = '/'

    return respuesta


urlpatterns = [

    # ==========================================
    # PWA
    # ==========================================

    path(
        'service-worker.js',
        service_worker_view,
        name='service_worker'
    ),

    path(
        'offline/',
        TemplateView.as_view(
            template_name='offline.html'
        ),
        name='offline'
    ),

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
