
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect
from jerd_cash_project.apps.cliente.models import SolicitudCredito
from jerd_cash_project.apps.loans.models import Prestamo
from .decorators import cliente_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from .validadores_archivos import validar_documento

from .models import SolicitudCredito


from datetime import timedelta
from decimal import Decimal

from .forms import (
    PerfilClienteForm,
    SolicitudCreditoForm,
    CIUDADES_POR_PAIS
)

from .models import (
    PerfilCliente,
    SolicitudCredito
)

from jerd_cash_project.apps.loans.models import (
    Prestamo,
    Cuota,
    Pago,
    PagoCuota,
)

from jerd_cash_project.apps.loans.services import (
    calcular_dias_mora,
    calcular_monto_mora,
)

from .ocr import (
    analizar_cedula,
    analizar_extracto_bancario
)


@cliente_required
def dashboard_view(request):
    return render(
        request,
        'cliente/dashboard.html'
    )


@cliente_required
def perfil_view(request):

    perfil, creado = PerfilCliente.objects.get_or_create(
        usuario=request.user,
        defaults={
            'ingresos_mensuales': 0,
            'gastos_mensuales': 0,
        }
    )

    if request.method == 'POST':

        form = PerfilClienteForm(
            request.POST,
            instance=perfil,
            usuario=request.user
        )

        if form.is_valid():

            form.save()

            return redirect('perfil')

    else:

        form = PerfilClienteForm(
            instance=perfil,
            usuario=request.user
        )

    return render(
        request,
        'cliente/perfil.html',
        {
            'form': form,
            'ciudades_por_pais': CIUDADES_POR_PAIS,
        }
    )


@cliente_required
def solicitar_credito_view(request):

    # ==========================================
    # VERIFICAR SOLICITUDES PENDIENTES
    # ==========================================

    solicitud_pendiente = SolicitudCredito.objects.filter(
        usuario=request.user,
        estado='PENDIENTE'
    ).exists()

    if solicitud_pendiente:

        messages.warning(
            request,
            'Ya tienes una solicitud de crédito pendiente. '
            'Debes esperar a que sea evaluada antes de solicitar otro crédito.'
        )

        return redirect('cliente_dashboard')

    # ==========================================
    # VERIFICAR CRÉDITOS ACTIVOS
    # ==========================================

    prestamos_activos = Prestamo.objects.filter(
        cliente=request.user,
        estado__in=[
            'aprobado',
            'desembolsado',
            'mora'
        ]
    )

    credito_activo = prestamos_activos.filter(
        cuotas__pagada=False
    ).exists()

    # También bloquear préstamos aprobados sin cuotas generadas.
    credito_sin_cuotas = prestamos_activos.filter(
        cuotas__isnull=True
    ).exists()

    if credito_activo or credito_sin_cuotas:

        messages.warning(
            request,
            'Actualmente tienes un crédito activo. '
            'Debes terminar de pagar todas tus cuotas '
            'antes de solicitar un nuevo crédito.'
        )

        return redirect('cliente_dashboard')

    # ==========================================
    # PROCESAR SOLICITUD
    # ==========================================

    if request.method == 'POST':

        form = SolicitudCreditoForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            # ==========================================
            # VALIDAR CÉDULA
            # ==========================================

            archivo_cedula = request.FILES.get('cedula')

            if not archivo_cedula:

                form.add_error(
                    'cedula',
                    'Debe adjuntar su cédula en formato PDF.'
                )

            else:

                try:

                    resultado_cedula = analizar_cedula(
                        archivo_cedula
                    )

                    if not resultado_cedula['es_cedula']:

                        form.add_error(
                            'cedula',
                            (
                                'El archivo que está intentando subir '
                                'no corresponde a una cédula. Debe subir '
                                'una cédula para continuar con el proceso.'
                            )
                        )

                except Exception:

                    form.add_error(
                        'cedula',
                        (
                            'No fue posible analizar el documento. '
                            'Verifique que el PDF sea válido.'
                        )
                    )

            # ==========================================
            # VALIDAR LOS TRES EXTRACTOS BANCARIOS
            # ==========================================

            extractos = [
                (
                    'extracto_bancario_1',
                    'primer'
                ),
                (
                    'extracto_bancario_2',
                    'segundo'
                ),
                (
                    'extracto_bancario_3',
                    'tercer'
                ),
            ]

            for campo, numero in extractos:

                archivo = request.FILES.get(campo)

                if not archivo:

                    form.add_error(
                        campo,
                        f'Debe adjuntar el {numero} extracto bancario.'
                    )

                    continue

                try:

                    resultado = analizar_extracto_bancario(
                        archivo
                    )

                    if not resultado['es_extracto']:

                        form.add_error(
                            campo,
                            (
                                f'La imagen del {numero} extracto '
                                'no parece corresponder a un '
                                'extracto bancario. Verifique el archivo.'
                            )
                        )

                except Exception:

                    form.add_error(
                        campo,
                        (
                            f'No fue posible analizar la imagen '
                            f'del {numero} extracto bancario.'
                        )
                    )

            # ==========================================
            # GUARDAR SOLICITUD
            # ==========================================

            # Verificar nuevamente que no existan errores.
            if form.is_valid():

                solicitud = form.save(
                    commit=False
                )

                solicitud.usuario = request.user

                # Guardar la solicitud y los archivos.
                # No se almacena el texto obtenido mediante OCR.
                solicitud.save()

                form.save_m2m()

                messages.success(
                    request,
                    'Tu solicitud de crédito fue enviada correctamente.'
                )

                return redirect(
                    'cliente_dashboard'
                )

    else:

        form = SolicitudCreditoForm()

    return render(
        request,
        'cliente/solicitar_credito.html',
        {
            'form': form
        }
    )
@cliente_required
def validar_cedula_ajax(request):

    if request.method != 'POST':

        return JsonResponse(
            {
                'valida': False,
                'mensaje': 'Método no permitido.'
            },
            status=405
        )

    archivo = request.FILES.get(
        'cedula'
    )

    if not archivo:

        return JsonResponse(
            {
                'valida': False,
                'mensaje': 'Debe seleccionar un archivo.'
            },
            status=400
        )

    if not archivo.name.lower().endswith('.pdf'):

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'La cédula debe estar en formato PDF.'
                )
            }
        )

    try:

        resultado = analizar_cedula(
            archivo
        )

        if resultado['es_cedula']:

            return JsonResponse(
                {
                    'valida': True,
                    'mensaje': (
                        'El documento parece corresponder '
                        'a una cédula.'
                    )
                }
            )

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'El archivo que está intentando subir '
                    'no corresponde a una cédula. Debe subir '
                    'una cédula para continuar con el proceso.'
                )
            }
        )

    except Exception:

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'No fue posible analizar el documento. '
                    'Verifique que el PDF sea válido.'
                )
            },
            status=500
        )



@cliente_required
def validar_extracto_ajax(request):

    if request.method != 'POST':

        return JsonResponse(
            {
                'valida': False,
                'mensaje': 'Método no permitido.'
            },
            status=405
        )

    archivo = request.FILES.get('extracto')

    if not archivo:

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'Debe seleccionar una imagen del '
                    'extracto bancario.'
                )
            },
            status=400
        )

    # Validación inicial de extensión.
    nombre_archivo = archivo.name.lower()

    extensiones_permitidas = (
        '.jpg',
        '.jpeg',
        '.png'
    )

    if not nombre_archivo.endswith(extensiones_permitidas):

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'El extracto debe ser una imagen '
                    'JPG, JPEG o PNG.'
                )
            },
            status=400
        )

    try:

        resultado = analizar_extracto_bancario(
            archivo
        )

        if resultado['es_extracto']:

            return JsonResponse(
                {
                    'valida': True,
                    'mensaje': (
                        'El extracto bancario fue validado '
                        'correctamente.'
                    )
                }
            )

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'La imagen no parece corresponder '
                    'a un extracto bancario. Verifique '
                    'el archivo e inténtelo nuevamente.'
                )
            }
        )

    except Exception:

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'No fue posible analizar la imagen '
                    'del extracto bancario.'
                )
            },
            status=500
        )


@cliente_required
def mis_solicitudes_view(request):

    solicitudes = SolicitudCredito.objects.filter(
        usuario=request.user
    ).order_by(
        '-fecha_solicitud'
    )

    return render(
        request,
        'cliente/mis_solicitudes.html',
        {
            'solicitudes': solicitudes
        }
    )


@cliente_required
def mis_creditos_view(request):

    # Fecha simulada para las pruebas.
    # En producción se puede utilizar timezone.localdate().
    today = timezone.datetime(
        2026,
        12,
        25
    ).date()

    prestamos = Prestamo.objects.filter(
        cliente=request.user
    ).prefetch_related(
        'cuotas'
    ).order_by(
        '-fecha_solicitud'
    )

    total_a_pagar = Decimal('0.00')
    cuotas_para_pagar = []

    for prestamo in prestamos:

        cuotas = list(
            prestamo.cuotas.all()
        )

        for cuota in cuotas:

            pago_rechazado = Pago.objects.filter(
                cuotas_pagadas__cuota=cuota,
                estado='rechazado'
            ).order_by(
                '-fecha_creacion'
            ).first()

            pago_pendiente_confirmacion = Pago.objects.filter(
                cuotas_pagadas__cuota=cuota,
                estado='pendiente_confirmacion'
            ).order_by(
                '-fecha_creacion'
            ).first()

            cuota.pago_rechazado = pago_rechazado
            cuota.pago_pendiente_confirmacion = (
                pago_pendiente_confirmacion
            )

        prestamo.tiene_pago_rechazado = any(
            cuota.pago_rechazado and not cuota.pagada
            for cuota in cuotas
        )

        cuotas_pagadas = [
            cuota for cuota in cuotas
            if cuota.pagada
        ]

        cuotas_pendientes = [
            cuota for cuota in cuotas
            if not cuota.pagada
        ]

        prestamo.cuotas_pagadas = len(
            cuotas_pagadas
        )

        prestamo.cuotas_pendientes = len(
            cuotas_pendientes
        )

        prestamo.total_cuotas = len(
            cuotas
        )

        prestamo.tiene_mora = False
        prestamo.cuotas_en_mora = 0
        prestamo.historial_mora = []

        # Historial de pagos que incluyeron mora.
        for cuota in cuotas:

            pagos_mora = PagoCuota.objects.filter(
                cuota=cuota,
                dias_mora__gt=0,
                pago__estado='exitoso'
            ).select_related(
                'pago'
            ).order_by(
                '-pago__fecha_pago'
            )

            for pago_cuota in pagos_mora:

                prestamo.historial_mora.append({
                    'numero_cuota': cuota.numero_cuota,
                    'fecha_vencimiento': cuota.fecha_vencimiento,
                    'fecha_pago': pago_cuota.pago.fecha_pago,
                    'dias_mora': pago_cuota.dias_mora,
                    'monto_mora': pago_cuota.monto_mora,
                    'monto_aplicado': pago_cuota.monto_aplicado,
                })

                if not hasattr(cuota, 'mora_historica'):
                    cuota.mora_historica = pago_cuota

        if not cuotas:

            prestamo.estado_pago = 'sin_cuotas'
            prestamo.proxima_cuota = None

        elif not cuotas_pendientes:

            prestamo.estado_pago = 'pagado'
            prestamo.proxima_cuota = None

        else:

            cuotas_vencidas = [
                cuota for cuota in cuotas_pendientes
                if cuota.fecha_vencimiento < today
            ]

            prestamo.estado_pago = (
                'mora' if cuotas_vencidas else 'al_dia'
            )

            prestamo.proxima_cuota = min(
                cuotas_pendientes,
                key=lambda cuota: cuota.fecha_vencimiento
            )

        # Fecha de corte y valores actuales.
        for cuota in cuotas_pendientes:

            fecha_corte = (
                cuota.fecha_vencimiento
                - timedelta(days=10)
            )

            cuota.fecha_corte = fecha_corte

            cuota.dias_mora_actual = calcular_dias_mora(
                cuota.fecha_vencimiento,
                today
            )

            cuota.monto_mora_actual = calcular_monto_mora(
                cuota.valor_cuota,
                cuota.dias_mora_actual
            )

            cuota.total_con_mora = (
                cuota.valor_cuota
                + cuota.monto_mora_actual
            )

            cuota.en_mora = cuota.dias_mora_actual > 0

            if cuota.en_mora:
                prestamo.tiene_mora = True
                prestamo.cuotas_en_mora += 1

            if today >= fecha_corte:

                total_a_pagar += cuota.total_con_mora
                cuotas_para_pagar.append(cuota)

    # Información del próximo pago.
    if cuotas_para_pagar:

        proxima_fecha_limite = min(
            cuota.fecha_vencimiento
            for cuota in cuotas_para_pagar
        )

        proxima_fecha_corte = (
            proxima_fecha_limite
            - timedelta(days=10)
        )

    else:

        proxima_fecha_limite = None
        proxima_fecha_corte = None

    return render(
        request,
        'cliente/mis_creditos.html',
        {
            'prestamos': prestamos,
            'today': today,
            'total_a_pagar': total_a_pagar,
            'proxima_fecha_corte': proxima_fecha_corte,
            'proxima_fecha_limite': proxima_fecha_limite,
        }
    )


@cliente_required
def pagar_view(request):

    from jerd_cash_project.apps.administrador.models import (
        ConfiguracionPago
    )

    # Fecha simulada para las pruebas.
    today = timezone.datetime(
        2026,
        12,
        25
    ).date()

    prestamos = Prestamo.objects.filter(
        cliente=request.user
    ).prefetch_related(
        'cuotas'
    )

    cuotas_para_pagar = []

    for prestamo in prestamos:

        cuotas_pendientes = [
            cuota
            for cuota in prestamo.cuotas.all()
            if not cuota.pagada
        ]

        for cuota in cuotas_pendientes:

            fecha_corte = (
                cuota.fecha_vencimiento
                - timedelta(days=10)
            )

            if today >= fecha_corte:
                cuotas_para_pagar.append(cuota)

    total_a_pagar = Decimal('0.00')

    for cuota in cuotas_para_pagar:

        dias_mora = calcular_dias_mora(
            cuota.fecha_vencimiento,
            today
        )

        monto_mora = calcular_monto_mora(
            cuota.valor_cuota,
            dias_mora
        )

        cuota.dias_mora_actual = dias_mora
        cuota.monto_mora_actual = monto_mora
        cuota.total_con_mora = (
            cuota.valor_cuota + monto_mora
        )

        total_a_pagar += cuota.total_con_mora

    configuracion = ConfiguracionPago.objects.order_by(
        '-fecha_actualizacion'
    ).first()

    pago_pendiente = Pago.objects.filter(
        cliente=request.user,
        estado='pendiente_confirmacion'
    ).order_by(
        '-fecha_creacion'
    ).first()

    if request.method == 'POST':

        if pago_pendiente:

            messages.warning(
                request,
                'Ya tienes un pago pendiente de confirmación. '
                'Debes esperar a que el administrador lo revise '
                'antes de enviar otro comprobante.'
            )

            return redirect('pagar')

        comprobante = request.FILES.get(
            'comprobante'
        )

        if not comprobante:

            messages.error(
                request,
                'Debes subir el comprobante de pago.'
            )

            return redirect('pagar')

                # ==========================================
        # VALIDAR COMPROBANTE DE PAGO
        # ==========================================

        try:

            extension = comprobante.name.lower()

            if extension.endswith('.pdf'):

                validar_documento(
                    comprobante,
                    'pdf'
                )

            elif extension.endswith(('.jpg', '.jpeg', '.png')):

                validar_documento(
                    comprobante,
                    'imagen'
                )

            else:

                raise ValidationError(
                    'El comprobante debe ser un archivo PDF, JPG o PNG.'
                )

        except ValidationError as error:

            messages.error(
                request,
                ' '.join(error.messages)
            )

            return redirect('pagar')

        if not cuotas_para_pagar:

            messages.error(
                request,
                'No tienes cuotas disponibles para pagar.'
            )

            return redirect('pagar')

        pago = Pago.objects.create(
            cliente=request.user,
            monto=total_a_pagar,
            comprobante=comprobante,
            estado='pendiente_confirmacion'
        )

        for cuota in cuotas_para_pagar:

            dias_mora = calcular_dias_mora(
                cuota.fecha_vencimiento,
                today
            )

            monto_mora = calcular_monto_mora(
                cuota.valor_cuota,
                dias_mora
            )

            monto_total_cuota = (
                cuota.valor_cuota + monto_mora
            )

            PagoCuota.objects.create(
                pago=pago,
                cuota=cuota,
                monto_aplicado=monto_total_cuota,
                dias_mora=dias_mora,
                monto_mora=monto_mora
            )

        # La cuota solo se marca como pagada
        # cuando el administrador confirma el pago.

        messages.success(
            request,
            'Tu comprobante fue enviado correctamente. '
            'El pago quedó pendiente de confirmación por parte '
            'del administrador.'
        )

        return redirect('pagar')

    pagos = Pago.objects.filter(
        cliente=request.user
    ).order_by(
        '-fecha_creacion'
    )

    return render(
        request,
        'cliente/pagar.html',
        {
            'cuotas_para_pagar': cuotas_para_pagar,
            'total_a_pagar': total_a_pagar,
            'configuracion': configuracion,
            'today': today,
            'pago_pendiente': pago_pendiente,
            'pagos': pagos,
        }
    )


@cliente_required
def estado_financiero_view(request):

    prestamos = Prestamo.objects.filter(
        cliente=request.user
    ).prefetch_related(
        'cuotas'
    ).order_by(
        '-fecha_solicitud'
    )

    creditos = []

    total_pagado_historico = Decimal('0.00')
    total_mora_historica = Decimal('0.00')
    total_cuotas_pagadas = 0
    total_cuotas_mora = 0

    for prestamo in prestamos:

        cuotas = list(
            prestamo.cuotas.all()
        )

        cuotas_pagadas = [
            cuota for cuota in cuotas
            if cuota.pagada
        ]

        pagos_cuota = PagoCuota.objects.filter(
            cuota__prestamo=prestamo,
            pago__estado='exitoso'
        ).select_related(
            'pago',
            'cuota'
        )

        total_pagado_credito = Decimal('0.00')
        total_mora_credito = Decimal('0.00')
        cuotas_pagadas_con_mora = 0
        pagos_mora_ids = set()

        for pago_cuota in pagos_cuota:

            total_pagado_credito += (
                pago_cuota.monto_aplicado
                or Decimal('0.00')
            )

            total_mora_credito += (
                pago_cuota.monto_mora
                or Decimal('0.00')
            )

            if pago_cuota.dias_mora > 0:

                cuotas_pagadas_con_mora += 1
                pagos_mora_ids.add(pago_cuota.pago_id)

        pagos_con_mora = len(
            pagos_mora_ids
        )

        fecha_inicio = prestamo.fecha_solicitud

        if cuotas:

            fecha_fin = max(
                cuota.fecha_vencimiento
                for cuota in cuotas
            )

        else:

            fecha_fin = None

        if cuotas and all(
            cuota.pagada for cuota in cuotas
        ):

            estado = 'pagado'

        else:

            estado = 'activo'

        total_pagado_historico += total_pagado_credito
        total_mora_historica += total_mora_credito
        total_cuotas_pagadas += len(cuotas_pagadas)
        total_cuotas_mora += cuotas_pagadas_con_mora

        creditos.append({
            'prestamo': prestamo,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'estado': estado,
            'total_cuotas': len(cuotas),
            'cuotas_pagadas': len(cuotas_pagadas),
            'cuotas_pendientes': (
                len(cuotas) - len(cuotas_pagadas)
            ),
            'total_pagado': total_pagado_credito,
            'total_mora': total_mora_credito,
            'cuotas_pagadas_con_mora': cuotas_pagadas_con_mora,
            'pagos_con_mora': pagos_con_mora,
        })

    total_creditos = len(creditos)

    creditos_activos = sum(
        1 for credito in creditos
        if credito['estado'] == 'activo'
    )

    creditos_pagados = sum(
        1 for credito in creditos
        if credito['estado'] == 'pagado'
    )

    return render(
        request,
        'cliente/estado_financiero.html',
        {
            'creditos': creditos,
            'total_creditos': total_creditos,
            'creditos_activos': creditos_activos,
            'creditos_pagados': creditos_pagados,
            'total_pagado_historico': total_pagado_historico,
            'total_mora_historica': total_mora_historica,
            'total_cuotas_pagadas': total_cuotas_pagadas,
            'total_cuotas_mora': total_cuotas_mora,
        }
    )


@cliente_required
def detalle_estado_financiero_view(request, prestamo_id):

    prestamo = get_object_or_404(
        Prestamo.objects.prefetch_related('cuotas'),
        id=prestamo_id,
        cliente=request.user
    )

    cuotas = list(
        prestamo.cuotas.all().order_by('numero_cuota')
    )

    pagos_cuota = PagoCuota.objects.filter(
        cuota__prestamo=prestamo,
        pago__estado='exitoso'
    ).select_related(
        'pago',
        'cuota'
    )

    pagos_por_cuota = {}

    total_pagado = Decimal('0.00')
    total_mora = Decimal('0.00')
    total_intereses = Decimal('0.00')
    cuotas_pagadas = 0
    cuotas_con_mora = 0

    for pago_cuota in pagos_cuota:

        cuota = pago_cuota.cuota

        total_pagado += (
            pago_cuota.monto_aplicado
            or Decimal('0.00')
        )

        total_mora += (
            pago_cuota.monto_mora
            or Decimal('0.00')
        )

        if cuota.pagada:
            cuotas_pagadas += 1

        if pago_cuota.dias_mora > 0:
            cuotas_con_mora += 1

        pagos_por_cuota.setdefault(
            cuota.id,
            []
        ).append(
            pago_cuota
        )

    for cuota in cuotas:

        if cuota.pagada:

            total_intereses += (
                cuota.interes
                or Decimal('0.00')
            )

    if cuotas:

        fecha_fin = max(
            cuota.fecha_vencimiento
            for cuota in cuotas
        )

    else:

        fecha_fin = None

    if cuotas and all(
        cuota.pagada for cuota in cuotas
    ):

        estado = 'pagado'

    else:

        estado = 'activo'

    return render(
        request,
        'cliente/detalle_estado_financiero.html',
        {
            'prestamo': prestamo,
            'cuotas': cuotas,
            'pagos_por_cuota': pagos_por_cuota,
            'fecha_fin': fecha_fin,
            'estado': estado,
            'total_pagado': total_pagado,
            'total_mora': total_mora,
            'total_intereses': total_intereses,
            'cuotas_pagadas': cuotas_pagadas,
            'cuotas_con_mora': cuotas_con_mora,
        }
    )

@login_required
def documento_solicitud_view(request, solicitud_id, tipo):

    solicitud = get_object_or_404(
        SolicitudCredito,
        id=solicitud_id
    )

    # Verificar que sea el propietario o un administrador.
    if (
        solicitud.usuario_id != request.user.id
        and request.user.role != 'administrador'
    ):
        raise Http404("Documento no encontrado.")

    # Campos permitidos.
    documentos = {
        'cedula': 'cedula',
        'recibo': 'recibo',
        'certificacion': 'certificacion_bancaria',
        'extracto_1': 'extracto_bancario_1',
        'extracto_2': 'extracto_bancario_2',
        'extracto_3': 'extracto_bancario_3',
    }

    if tipo not in documentos:
        raise Http404("Documento no encontrado.")

    archivo = getattr(
        solicitud,
        documentos[tipo]
    )

    if not archivo:
        raise Http404("Documento no disponible.")

    try:
        archivo.open('rb')
    except (OSError, ValueError):
        raise Http404("Documento no disponible.")

    respuesta = FileResponse(
        archivo,
        as_attachment=False
    )

    respuesta['X-Content-Type-Options'] = 'nosniff'
    respuesta['Cache-Control'] = 'private, no-store'

    return respuesta