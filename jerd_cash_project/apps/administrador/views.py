from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from jerd_cash_project.apps.cliente.models import SolicitudCredito


@login_required
def dashboard_view(request):
    return render(
        request,
        'administrador/dashboard.html'
    )


@login_required
def solicitudes_view(request):
    solicitudes = SolicitudCredito.objects.select_related(
        'usuario'
    ).order_by('-fecha_solicitud')

    return render(
        request,
        'administrador/solicitudes.html',
        {
            'solicitudes': solicitudes
        }
    )

@login_required
def solicitud_detalle_view(request, solicitud_id):
    solicitud = SolicitudCredito.objects.select_related(
        'usuario'
    ).get(id=solicitud_id)

    return render(
        request,
        'administrador/solicitud_detalle.html',
        {
            'solicitud': solicitud
        }
    )