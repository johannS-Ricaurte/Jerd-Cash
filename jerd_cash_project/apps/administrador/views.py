from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from jerd_cash_project.apps.cliente.models import SolicitudCredito
from jerd_cash_project.apps.users.email_service import enviar_notificacion

from jerd_cash_project.apps.loans.models import (
    Prestamo,
    Cuota,
    Pago,
    PagoCuota,
)

from jerd_cash_project.apps.loans.services import (
    calcular_score_deterministico,
    calcular_detalle_score,
    calcular_tabla_amortizacion
)

from jerd_cash_project.apps.administrador.models import ConfiguracionPago


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
        SolicitudCredito.objects.select_related(
            'usuario'
        ),
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
        calcular_score_deterministico(
            usuario,
            solicitud
        )
    )

    detalle_score = calcular_detalle_score(
        usuario,
        solicitud
    )


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

    score, nivel_riesgo, tasa_interes = (
        calcular_score_deterministico(
            usuario,
            solicitud
        )
    )

    if tasa_interes is None:

        messages.error(
            request,
            'No se puede aprobar la solicitud porque no existe una tasa de interés válida para este nivel de riesgo.'
        )

        return redirect(
            'administrador_solicitud_detalle',
            solicitud_id=solicitud.id
        )

    plazo_meses = solicitud.plazo_meses

    prestamo = Prestamo.objects.create(
        cliente=usuario,
        monto_solicitado=solicitud.monto_solicitado,
        plazo_meses=plazo_meses,
        tasa_interes_mensual=tasa_interes,
        score_calculado=score,
        nivel_riesgo=nivel_riesgo,
        estado='aprobado'
    )

    tabla = calcular_tabla_amortizacion(
        monto=prestamo.monto_solicitado,
        tasa_mensual=prestamo.tasa_interes_mensual,
        plazo_meses=prestamo.plazo_meses
    )

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

    solicitud.estado = 'APROBADA'
    solicitud.save()

    enviar_notificacion(
        destinatario=usuario.email,
        asunto=f"Tu crédito #{prestamo.id} ha sido aprobado",
        mensaje=(
            f"Hola {usuario.first_name or usuario.username},\n\n"
            f"¡Buenas noticias! Tu solicitud de crédito "
            f"#{solicitud.id} ha sido aprobada.\n\n"
            f"Crédito: #{prestamo.id}\n"
            f"Monto aprobado: ${prestamo.monto_solicitado:,.2f}\n"
            f"Plazo: {prestamo.plazo_meses} meses\n"
            f"Tasa de interés mensual: "
            f"{prestamo.tasa_interes_mensual}%\n\n"
            "Puedes ingresar a JERD-Cash para consultar "
            "el detalle de tu crédito y sus cuotas.\n\n"
            "Equipo JERD-Cash"
        ),
    )

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

    usuario = solicitud.usuario

    enviar_notificacion(
        destinatario=usuario.email,
        asunto=f"Actualización de tu solicitud #{solicitud.id}",
        mensaje=(
            f"Hola {usuario.first_name or usuario.username},\n\n"
            f"Te informamos que tu solicitud de crédito "
            f"#{solicitud.id} ha sido rechazada.\n\n"
            "Puedes ingresar a JERD-Cash para consultar "
            "el estado de tu solicitud o contactar al equipo "
            "responsable si necesitas más información.\n\n"
            "Gracias por tu interés.\n"
            "Equipo JERD-Cash"
        ),
    )

    messages.success(
        request,
        f'La solicitud #{solicitud.id} fue rechazada.'
    )

    return redirect(
        'administrador_solicitud_detalle',
        solicitud_id=solicitud.id
    )

@login_required
def creditos_view(request):

    prestamos = Prestamo.objects.filter(
        estado__in=[
            'aprobado',
            'desembolsado',
            'mora',
            'pagado'
        ]
    ).select_related(
        'cliente'
    ).prefetch_related(
        'cuotas'
    ).order_by(
        'cliente__first_name',
        'cliente__last_name'
    )

    # Fecha simulada actual del sistema
    today = timezone.datetime(
        2026,
        12,
        25
    ).date()

    clientes_data = {}

    for prestamo in prestamos:

        cliente = prestamo.cliente

        if cliente.id not in clientes_data:

            nombre = (
                f"{cliente.first_name} {cliente.last_name}"
            ).strip()

            if not nombre:
                nombre = "Cliente sin nombre registrado"

            clientes_data[cliente.id] = {
                'cliente': cliente,
                'nombre': nombre,
                'cantidad_creditos': 0,
                'total_creditos': 0,
                'deuda_pendiente': 0,
                'cuotas_pagadas': 0,
                'cuotas_totales': 0,
                'prestamos': [],
                'tiene_cuotas_vencidas': False,
                'cuotas_vencidas': 0,
                'estado_pago': 'al_dia',
            }

        datos = clientes_data[cliente.id]

        datos['cantidad_creditos'] += 1

        datos['total_creditos'] += prestamo.monto_solicitado

        cuotas = list(
            prestamo.cuotas.all()
        )

        datos['cuotas_totales'] += len(cuotas)

        datos['cuotas_pagadas'] += sum(
            1
            for cuota in cuotas
            if cuota.pagada
        )

        datos['deuda_pendiente'] += sum(
            cuota.valor_cuota
            for cuota in cuotas
            if not cuota.pagada
        )

        # Detectar cuotas vencidas
        cuotas_vencidas_credito = sum(
            1
            for cuota in cuotas
            if not cuota.pagada
            and cuota.fecha_vencimiento < today
        )

        print("===================================")
        print("REVISION CUOTAS")
        print("Cliente:", datos['nombre'])
        print("Préstamo:", prestamo.id)
        print("Hoy:", today)

        for cuota in cuotas:

            print(
                "Cuota:",
                cuota.numero_cuota,
                "| Vencimiento:",
                cuota.fecha_vencimiento,
                "| Pagada:",
                cuota.pagada,
                "| ¿Vencida?:",
                (
                    not cuota.pagada
                    and cuota.fecha_vencimiento < today
                )
            )

        print(
            "Total cuotas vencidas:",
            cuotas_vencidas_credito
        )

        print("===================================")

        if cuotas_vencidas_credito > 0:

            datos['tiene_cuotas_vencidas'] = True

            datos['cuotas_vencidas'] += cuotas_vencidas_credito

        datos['prestamos'].append(
            prestamo
        )


    # Revisar pagos pendientes de confirmación
    for cliente_id, datos in clientes_data.items():

        cliente = datos['cliente']

        pagos_pendientes = Pago.objects.filter(
            cliente=cliente,
            estado='pendiente_confirmacion'
        ).prefetch_related(
            'cuotas_pagadas__cuota'
        ).order_by(
            '-fecha_creacion'
        )

        datos['pagos_pendientes'] = pagos_pendientes


    # Obtener todos los pagos pendientes de verificación
    pagos_por_verificar = Pago.objects.filter(
        estado='pendiente_confirmacion'
    ).prefetch_related(
        'cliente',
        'cuotas_pagadas__cuota'
    ).order_by(
        '-fecha_creacion'
    )

    # Determinar el estado general de pago de cada cliente
    for cliente_id, datos in clientes_data.items():

        if datos['tiene_cuotas_vencidas']:

            datos['estado_pago'] = 'mora'

        elif datos['pagos_pendientes'].exists():

            datos['estado_pago'] = 'pago_pendiente'

        elif (
            datos['cuotas_totales'] > 0
            and datos['cuotas_pagadas'] == datos['cuotas_totales']
        ):

            datos['estado_pago'] = 'pagado'

        else:

            datos['estado_pago'] = 'al_dia'


    print("===================================")
    print("ESTADOS DE PAGO")
    print("===================================")

    for cliente_id, datos in clientes_data.items():

        print(
            datos['nombre'],
            "| Estado:",
            datos['estado_pago'],
            "| Cuotas vencidas:",
            datos['cuotas_vencidas'],
            "| Cuotas pagadas:",
            datos['cuotas_pagadas'],
            "| Cuotas totales:",
            datos['cuotas_totales']
        )

    print("===================================")


    clientes = list(
        clientes_data.values()
    )

    return render(
        request,
        'administrador/creditos.html',
        {
            'clientes': clientes,
            'today': today,
            'pagos_por_verificar': pagos_por_verificar,
        }
    )

@login_required
def credito_detalle_view(request, prestamo_id):

    prestamo = get_object_or_404(
        Prestamo.objects.select_related(
            'cliente'
        ).prefetch_related(
            'cuotas'
        ),
        id=prestamo_id
    )

    cliente = prestamo.cliente

    prestamos_cliente = Prestamo.objects.filter(
        cliente=cliente
    ).select_related(
        'cliente'
    ).prefetch_related(
        'cuotas'
    ).order_by(
        '-fecha_solicitud'
    )

    pagos_pendientes = Pago.objects.filter(
        cliente=cliente,
        estado='pendiente_confirmacion'
    ).prefetch_related(
        'cuotas_pagadas__cuota'
    ).order_by(
        '-fecha_creacion'
    )

    # Fecha simulada actual del sistema
    today = timezone.datetime(
        2026,
        12,
        25
    ).date()

    # Analizar estado de cada cuota
    cuotas = list(
        prestamo.cuotas.all()
    )

    cuotas_pagadas = sum(
        1
        for cuota in cuotas
        if cuota.pagada
    )

    cuotas_totales = len(cuotas)

    # Identificar cuotas que tienen un pago
    # pendiente de confirmación
    cuotas_pago_pendiente = set()

    for pago in pagos_pendientes:

        for pago_cuota in pago.cuotas_pagadas.all():

            cuotas_pago_pendiente.add(
                pago_cuota.cuota.id
            )

    # Determinar estado de cada cuota
    for cuota in cuotas:

        # Buscar si la cuota tuvo un pago exitoso con mora
        cuota.mora_historica = PagoCuota.objects.filter(
            cuota=cuota,
            dias_mora__gt=0,
            pago__estado='exitoso'
        ).order_by(
            '-pago__fecha_pago'
        ).first()

        if cuota.pagada:

            cuota.estado_admin = 'pagada'

        elif cuota.id in cuotas_pago_pendiente:

            cuota.estado_admin = 'pago_pendiente'

        elif cuota.fecha_vencimiento < today:

            cuota.estado_admin = 'vencida'

        else:

            cuota.estado_admin = 'pendiente'

    print("===================================")
    print("PAGO PENDIENTE - CUOTAS ASOCIADAS")
    print(cuotas_pago_pendiente)

    for cuota in cuotas:
        print(
            "Cuota:",
            cuota.numero_cuota,
            "| ID:",
            cuota.id,
            "| Estado:",
            cuota.estado_admin
        )

    print("===================================")

    # Verificar si el crédito tiene cuotas vencidas
    tiene_cuotas_vencidas = any(
        cuota.estado_admin == 'vencida'
        for cuota in cuotas
    )

    # Contar cuotas vencidas
    cuotas_vencidas = sum(
        1
        for cuota in cuotas
        if cuota.estado_admin == 'vencida'
    )

    nombre_cliente = (
        f"{cliente.first_name} {cliente.last_name}"
    ).strip()

    if not nombre_cliente:
        nombre_cliente = "Cliente sin nombre registrado"

    return render(
        request,
        'administrador/credito_detalle.html',
        {
            'prestamo': prestamo,
            'cliente': cliente,
            'nombre_cliente': nombre_cliente,
            'prestamos_cliente': prestamos_cliente,
            'pagos_pendientes': pagos_pendientes,

            # Información de estados
            'today': today,
            'tiene_cuotas_vencidas': tiene_cuotas_vencidas,
            'cuotas_vencidas': cuotas_vencidas,
            'cuotas_pagadas': cuotas_pagadas,
            'cuotas_totales': cuotas_totales,
        }
    )

@login_required
def aprobar_pago_view(request, pago_id):

    if request.method != 'POST':
        return redirect('administrador_creditos')

    pago = get_object_or_404(
        Pago.objects.prefetch_related(
            'cuotas_pagadas__cuota'
        ),
        id=pago_id
    )

    if pago.estado != 'pendiente_confirmacion':

        messages.warning(
            request,
            'Este pago ya fue procesado anteriormente.'
        )

        return redirect(
            'administrador_credito_detalle',
            prestamo_id=pago.cuotas_pagadas.first().cuota.prestamo.id
        )

    with transaction.atomic():

        pago.estado = 'exitoso'
        ##pago.fecha_pago = timezone.now()
        pago.fecha_pago = timezone.datetime(
            2026,
            12,
            25,
            tzinfo=timezone.get_current_timezone()
        )
        pago.motivo_rechazo = ''
        pago.save()

        for pago_cuota in pago.cuotas_pagadas.all():

            cuota = pago_cuota.cuota

            cuota.pagada = True
            cuota.save(update_fields=['pagada'])

    pago_cuota = pago.cuotas_pagadas.first()

    if pago_cuota:
        usuario = pago_cuota.cuota.prestamo.cliente

        enviar_notificacion(
            destinatario=usuario.email,
            asunto=f"Tu pago #{pago.id} ha sido aprobado",
            mensaje=(
                f"Hola {usuario.first_name or usuario.username},\n\n"
                f"Tu pago #{pago.id} ha sido aprobado correctamente.\n\n"
                f"Valor del pago: ${pago.monto:,.2f}\n\n"
                "El sistema ha actualizado el estado de las cuotas "
                "asociadas a este pago. Puedes ingresar a JERD-Cash "
                "para consultar el detalle de tu crédito.\n\n"
                "Equipo JERD-Cash"
            ),
        )

    messages.success(
        request,
        f'El pago #{pago.id} fue aprobado correctamente.'
    )

    return redirect(
        'administrador_credito_detalle',
        prestamo_id=pago_cuota.cuota.prestamo.id
    )


@login_required
def rechazar_pago_view(request, pago_id):

    if request.method != 'POST':
        return redirect('administrador_creditos')

    pago = get_object_or_404(
        Pago.objects.prefetch_related(
            'cuotas_pagadas__cuota'
        ),
        id=pago_id
    )

    if pago.estado != 'pendiente_confirmacion':

        messages.warning(
            request,
            'Este pago ya fue procesado anteriormente.'
        )

        pago_cuota = pago.cuotas_pagadas.first()

        if pago_cuota:
            return redirect(
                'administrador_credito_detalle',
                prestamo_id=pago_cuota.cuota.prestamo.id
            )

        return redirect('administrador_creditos')

    motivo = request.POST.get(
        'motivo_rechazo',
        ''
    ).strip()

    if not motivo:

        messages.error(
            request,
            'Debes indicar el motivo del rechazo.'
        )

        pago_cuota = pago.cuotas_pagadas.first()

        if pago_cuota:
            return redirect(
                'administrador_credito_detalle',
                prestamo_id=pago_cuota.cuota.prestamo.id
            )

        return redirect('administrador_creditos')

    pago.estado = 'rechazado'
    pago.motivo_rechazo = motivo
    pago.fecha_pago = None
    pago.save(
        update_fields=[
            'estado',
            'motivo_rechazo',
            'fecha_pago',
            'fecha_actualizacion'
        ]
    )

    messages.success(
        request,
        f'El pago #{pago.id} fue rechazado correctamente.'
    )

    pago_cuota = pago.cuotas_pagadas.first()

    if pago_cuota:
        usuario = pago_cuota.cuota.prestamo.cliente

        enviar_notificacion(
            destinatario=usuario.email,
            asunto=f"Tu pago #{pago.id} ha sido rechazado",
            mensaje=(
                f"Hola {usuario.first_name or usuario.username},\n\n"
                f"Tu pago #{pago.id} ha sido rechazado.\n\n"
                f"Motivo informado: {pago.motivo_rechazo}\n\n"
                "Por favor, revisa el motivo indicado y las "
                "instrucciones de pago en JERD-Cash. Si necesitas "
                "ayuda, contacta al equipo responsable.\n\n"
                "Equipo JERD-Cash"
            ),
        )

    if pago_cuota:
        return redirect(
            'administrador_credito_detalle',
            prestamo_id=pago_cuota.cuota.prestamo.id
        )

    return redirect('administrador_creditos')



@login_required
def clientes_view(request):

    from django.contrib.auth import get_user_model
    from django.db.models import Q

    Usuario = get_user_model()

    busqueda = request.GET.get('buscar', '').strip()

    # Obtener usuarios que tengan créditos registrados.
    clientes_ids = Prestamo.objects.values_list(
        'cliente_id',
        flat=True
    ).distinct()

    clientes = Usuario.objects.filter(
        id__in=clientes_ids
    )

    # Buscar por nombre, apellido, usuario o identificación
    if busqueda:
        filtros = (
            Q(first_name__icontains=busqueda)
            | Q(last_name__icontains=busqueda)
            | Q(username__icontains=busqueda)
        )

        # Agregar búsqueda por identificación si el modelo
        # tiene un campo de cédula.
        campos_usuario = [
            campo.name for campo in Usuario._meta.get_fields()
        ]

        if 'cedula' in campos_usuario:
            filtros |= Q(cedula__icontains=busqueda)

        clientes = clientes.filter(filtros)

    clientes = clientes.order_by(
        'first_name',
        'last_name'
    )

    datos_clientes = []

    for cliente in clientes:

        prestamos = Prestamo.objects.filter(
            cliente=cliente
        ).prefetch_related('cuotas')

        cantidad_creditos = prestamos.count()

        creditos_pagados = prestamos.filter(
            estado='pagado'
        ).count()

        cuotas_totales = 0
        cuotas_pagadas = 0
        cuotas_pagadas_con_mora = 0

        for prestamo in prestamos:

            cuotas = list(prestamo.cuotas.all())

            cuotas_totales += len(cuotas)

            cuotas_pagadas += sum(
                1 for cuota in cuotas if cuota.pagada
            )

            for cuota in cuotas:

                if not cuota.pagada:
                    continue

                tuvo_mora = PagoCuota.objects.filter(
                    cuota=cuota,
                    dias_mora__gt=0,
                    pago__estado='exitoso'
                ).exists()

                if tuvo_mora:
                    cuotas_pagadas_con_mora += 1

        nombre = (
            f'{cliente.first_name} {cliente.last_name}'
        ).strip()

        if not nombre:
            nombre = cliente.username

        datos_clientes.append({
            'cliente': cliente,
            'nombre': nombre,
            'cantidad_creditos': cantidad_creditos,
            'creditos_pagados': creditos_pagados,
            'cuotas_totales': cuotas_totales,
            'cuotas_pagadas': cuotas_pagadas,
            'cuotas_pagadas_con_mora': cuotas_pagadas_con_mora,
        })

    return render(
        request,
        'administrador/clientes.html',
        {
            'clientes': datos_clientes,
            'busqueda': busqueda,
        }
    )


@login_required
def cliente_detalle_view(request, cliente_id):

    from django.contrib.auth import get_user_model

    Usuario = get_user_model()

    cliente = get_object_or_404(
        Usuario,
        id=cliente_id
    )

    prestamos = Prestamo.objects.filter(
        cliente=cliente
    ).prefetch_related(
        'cuotas'
    ).order_by(
        '-fecha_solicitud'
    )

    cantidad_creditos = prestamos.count()

    creditos_pagados = prestamos.filter(
        estado='pagado'
    ).count()

    cuotas_totales = 0
    cuotas_pagadas = 0
    cuotas_pagadas_con_mora = 0
    total_mora_pagada = 0
    total_pagado = 0

    for prestamo in prestamos:

        cuotas = list(prestamo.cuotas.all())

        prestamo.cuotas_pagadas_count = sum(
            1 for cuota in cuotas if cuota.pagada
        )

        cuotas_totales += len(cuotas)

        for cuota in cuotas:

            if not cuota.pagada:
                continue

            cuotas_pagadas += 1

            pagos_cuota = PagoCuota.objects.filter(
                cuota=cuota,
                pago__estado='exitoso'
            ).select_related('pago')

            for pago_cuota in pagos_cuota:

                total_pagado += pago_cuota.monto_aplicado

                if pago_cuota.dias_mora > 0:

                    cuotas_pagadas_con_mora += 1
                    total_mora_pagada += pago_cuota.monto_mora

    nombre = (
        f'{cliente.first_name} {cliente.last_name}'
    ).strip()

    if not nombre:
        nombre = cliente.username

    context = {
        'cliente': cliente,
        'nombre_cliente': nombre,
        'prestamos': prestamos,
        'cantidad_creditos': cantidad_creditos,
        'creditos_pagados': creditos_pagados,
        'cuotas_totales': cuotas_totales,
        'cuotas_pagadas': cuotas_pagadas,
        'cuotas_pagadas_con_mora': cuotas_pagadas_con_mora,
        'total_mora_pagada': total_mora_pagada,
        'total_pagado': total_pagado,
    }

    return render(
        request,
        'administrador/cliente_detalle.html',
        context
    )



@login_required
def configuracion_pago_view(request):
    from jerd_cash_project.apps.administrador.models import ConfiguracionPago

    if getattr(request.user, 'role', '') != 'administrador':
        messages.error(
            request,
            'No tienes permisos para modificar la configuración de pago.'
        )
        return redirect('home')

    configuracion = ConfiguracionPago.objects.order_by(
        '-fecha_actualizacion'
    ).first()

    if request.method == 'POST':
        entidad = request.POST.get('entidad', '').strip()
        llave = request.POST.get('llave', '').strip()
        titular = request.POST.get('titular', '').strip()
        instrucciones = request.POST.get('instrucciones', '').strip()
        qr = request.FILES.get('qr')

        if not all([entidad, llave, titular]):
            messages.error(
                request,
                'Completa la entidad, la llave de transferencia y el titular.'
            )
        elif configuracion is None and not qr:
            messages.error(
                request,
                'Debes subir un código QR para crear la configuración inicial.'
            )
        else:
            if configuracion is None:
                configuracion = ConfiguracionPago()

            configuracion.entidad = entidad
            configuracion.llave = llave
            configuracion.titular = titular
            configuracion.instrucciones = instrucciones

            if qr:
                configuracion.qr = qr

            configuracion.save()

            messages.success(
                request,
                'La configuración de pago se guardó correctamente.'
            )
            return redirect('administrador_configuracion_pago')

    return render(
        request,
        'administrador/configuracion_pago.html',
        {'configuracion': configuracion}
    )
