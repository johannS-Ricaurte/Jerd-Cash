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

    path(
        'creditos/',
        views.creditos_view,
        name='administrador_creditos'
    ),

    path(
        'creditos/',
        views.creditos_view,
        name='administrador_creditos'
    ),

    path(
        'creditos/<int:prestamo_id>/',
        views.credito_detalle_view,
        name='administrador_credito_detalle'
    ),

    path(
        'pagos/<int:pago_id>/aprobar/',
        views.aprobar_pago_view,
        name='administrador_aprobar_pago'
    ),

    path(
        'pagos/<int:pago_id>/rechazar/',
        views.rechazar_pago_view,
        name='administrador_rechazar_pago'
    ),

    path(
        'clientes/',
        views.clientes_view,
        name='administrador_clientes'
    ),

    path(
        'clientes/<int:cliente_id>/',
        views.cliente_detalle_view,
        name='administrador_cliente_detalle'
    ),

        
    path(
        'configuracion-pago/',
        views.configuracion_pago_view,
        name='administrador_configuracion_pago'
    ),

    


]