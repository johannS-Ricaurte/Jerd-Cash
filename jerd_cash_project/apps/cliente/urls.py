from django.urls import path
from . import views


urlpatterns = [

    path(
        '',
        views.dashboard_view,
        name='cliente_dashboard'
    ),

    path(
        'perfil/',
        views.perfil_view,
        name='perfil'
    ),

    path(
        'solicitar-credito/',
        views.solicitar_credito_view,
        name='solicitar_credito'
    ),

    path(
        'mis-solicitudes/',
        views.mis_solicitudes_view,
        name='mis_solicitudes'
    ),

    path(
        'validar-cedula/',
        views.validar_cedula_ajax,
        name='validar_cedula'
    ),

    path(
        'validar-extracto/',
        views.validar_extracto_ajax,
        name='validar_extracto'
    ),

    path(
    'mis-creditos/',
    views.mis_creditos_view,
    name='mis_creditos'
    ),

    path(
    'pagar/', 
    views.pagar_view, 
    name='pagar'
    ),

    path(
    'estado-financiero/',
    views.estado_financiero_view,
    name='estado_financiero'
    ),

    path(
    'estado-financiero/<int:prestamo_id>/',
    views.detalle_estado_financiero_view,
    name='detalle_estado_financiero'
    ),

]
