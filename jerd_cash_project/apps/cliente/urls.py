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

]
