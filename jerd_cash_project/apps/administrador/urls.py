from django.urls import path

from . import views


urlpatterns = [

    path(
        '',
        views.dashboard_view,
        name='administrador_dashboard'
    ),

    path(
        'solicitudes/',
        views.solicitudes_view,
        name='administrador_solicitudes'
    ),

    path(
        'solicitudes/<int:solicitud_id>/',
        views.solicitud_detalle_view,
        name='administrador_solicitud_detalle'
    ),

    path(
        'solicitudes/<int:solicitud_id>/aprobar/',
        views.aprobar_solicitud_view,
        name='administrador_aprobar_solicitud'
    ),

    path(
        'solicitudes/<int:solicitud_id>/rechazar/',
        views.rechazar_solicitud_view,
        name='administrador_rechazar_solicitud'
    ),

]