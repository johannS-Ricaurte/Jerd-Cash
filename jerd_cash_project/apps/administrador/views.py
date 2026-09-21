from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from jerd_cash_project.apps.cliente.models import SolicitudCredito
from jerd_cash_project.apps.loans.models import Prestamo, Cuota

from jerd_cash_project.apps.loans.services import (
    calcular_score_deterministico,
    calcular_detalle_score,
    calcular_tabla_amortizacion
)

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
    ).order_by(
        '-fecha_solicitud'
    )

    return render(
        request,
        'administrador/solicitudes.html',
        {
            'solicitudes': solicitudes
        }
    )


@login_required
def solicitud_detalle_view(request, solicitud_id):

    solicitud = get_object_or_404(
        SolicitudCredito.objects.select_related('usuario'),
        id=solicitud_id
    )

    usuario = solicitud.usuario

    prestamos_anteriores = Prestamo.objects.filter(
        cliente=usuario
    ).prefetch_related(
        'cuotas'
    ).order_by(
        '-fecha_solicitud'
    )

    es_cliente_nuevo = not prestamos_anteriores.exists()

    score, nivel_riesgo, tasa_interes = (
        calcular_score_deterministico(usuario, solicitud)
    )

    detalle_score = calcular_detalle_score(usuario, solicitud)

    context = {
        'solicitud': solicitud,
        'es_cliente_nuevo': es_cliente_nuevo,
        'prestamos_anteriores': prestamos_anteriores,
        'score': score,
        'nivel_riesgo': nivel_riesgo,
        'tasa_interes': tasa_interes,
        'detalle_score': detalle_score,
    }

    return render(
        request,
        'administrador/solicitud_detalle.html',
        context
    )


@login_required
def aprobar_solicitud_view(request, solicitud_id):

    if request.method != 'POST':
        return redirect(
            'administrador_solicitud_detalle',
            solicitud_id=solicitud_id
        )

    solicitud = get_object_or_404(
        SolicitudCredito,
        id=solicitud_id
    )

    # Evitamos aprobar una solicitud que ya fue procesada
    if solicitud.estado != 'PENDIENTE':

        messages.warning(
            request,
            'Esta solicitud ya fue procesada anteriormente.'
        )

        return redirect(
            'administrador_solicitud_detalle',
            solicitud_id=solicitud.id
        )

    usuario = solicitud.usuario

    # Calculamos nuevamente el score al momento de aprobar
    score, nivel_riesgo, tasa_interes = (
        calcular_score_deterministico(usuario, solicitud)
    )

    # Si el sistema no puede determinar una tasa,
    # no permitimos crear el préstamo.
    if tasa_interes is None:

        messages.error(
            request,
            'No se puede aprobar la solicitud porque no existe una tasa de interés válida para este nivel de riesgo.'
        )

        return redirect(
            'administrador_solicitud_detalle',
            solicitud_id=solicitud.id
        )

    # Usamos el plazo seleccionado por el cliente
    plazo_meses = solicitud.plazo_meses


    # Creamos el préstamo
    prestamo = Prestamo.objects.create(
        cliente=usuario,
        monto_solicitado=solicitud.monto_solicitado,
        plazo_meses=plazo_meses,
        tasa_interes_mensual=tasa_interes,
        score_calculado=score,
        nivel_riesgo=nivel_riesgo,
        estado='aprobado'
    )

    # Calculamos la tabla de amortización
    tabla = calcular_tabla_amortizacion(
        monto=prestamo.monto_solicitado,
        tasa_mensual=prestamo.tasa_interes_mensual,
        plazo_meses=prestamo.plazo_meses
    )

    # Creamos las cuotas
    for fila in tabla:

        Cuota.objects.create(
            prestamo=prestamo,
            numero_cuota=fila['numero_cuota'],
            fecha_vencimiento=fila['fecha_vencimiento'],
            valor_cuota=fila['valor_cuota'],
            interes=fila['interes'],
            abono_capital=fila['abono_capital'],
            saldo_pendiente=fila['saldo_pendiente'],
            pagada=False
        )

    # Actualizamos la solicitud
    solicitud.estado = 'APROBADA'
    solicitud.save()

    messages.success(
        request,
        f'La solicitud #{solicitud.id} fue aprobada, se creó el préstamo #{prestamo.id} y se generaron {len(tabla)} cuotas.'
    )

    return redirect(
        'administrador_solicitud_detalle',
        solicitud_id=solicitud.id
    )

@login_required
def rechazar_solicitud_view(request, solicitud_id):

    if request.method != 'POST':
        return redirect(
            'administrador_solicitud_detalle',
            solicitud_id=solicitud_id
        )

    solicitud = get_object_or_404(
        SolicitudCredito,
        id=solicitud_id
    )

    # Evitamos modificar una solicitud que ya fue procesada
    if solicitud.estado != 'PENDIENTE':

        messages.warning(
            request,
            'Esta solicitud ya fue procesada anteriormente.'
        )

        return redirect(
            'administrador_solicitud_detalle',
            solicitud_id=solicitud.id
        )

    solicitud.estado = 'RECHAZADA'
    solicitud.save()

    messages.success(
        request,
        f'La solicitud #{solicitud.id} fue rechazada.'
    )

    return redirect(
        'administrador_solicitud_detalle',
        solicitud_id=solicitud.id
    )