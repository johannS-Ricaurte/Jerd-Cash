# apps/loans/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from decimal import Decimal
from .services import calcular_tabla_amortizacion, calcular_score_deterministico, calcular_score_simulador
from types import SimpleNamespace
from jerd_cash_project.apps.cliente.decorators import cliente_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404

from .models import Pago

def obtener_maximo_cuotas(monto):

    if monto < 100000 or monto > 1000000:
        return 0

    if monto < 200000:
        return 1
    if monto < 300000:
        return 2
    if monto < 400000:
        return 3
    if monto < 500000:
        return 4
    if monto < 600000:
        return 5
    if monto < 700000:
        return 6
    if monto < 800000:
        return 7
    if monto < 900000:
        return 8
    if monto < 1000000:
        return 10

    return 12

@cliente_required
def simulador_view(request):
    return render(request, 'loans/simulador.html', {'titulo': 'Simulador de Crédito'})

def simulador_publico_view(request):
    """
    Simulador público de crédito.

    No requiere autenticación.
    """

    context = {
        'titulo': 'Simulador de Crédito',
    }

    if request.method == 'POST':

        try:

            ingresos = Decimal(
                request.POST.get('ingresos', '0').replace('.', '').replace(',', '')
            )

            gastos = Decimal(
                request.POST.get('gastos', '0').replace('.', '').replace(',', '')
            )

            monto = Decimal(
                request.POST.get('monto', '0').replace('.', '').replace(',', '')
            )

            plazo = int(
                request.POST.get(
                    'plazo',
                    '0'
                )
            )

            # =========================
            # VALIDACIONES
            # =========================

            if ingresos <= 0:

                context['error'] = (
                    'Los ingresos mensuales deben ser '
                    'mayores a $0.'
                )

            elif gastos < 0:

                context['error'] = (
                    'Los gastos mensuales no pueden '
                    'ser negativos.'
                )

            elif monto < 100000 or monto > 1000000:

                context['error'] = (
                    'El monto del crédito debe estar '
                    'entre $100.000 y $1.000.000.'
                )

            elif plazo < 1 or plazo > obtener_maximo_cuotas(monto):

                maximo = obtener_maximo_cuotas(monto)

                context['error'] = (
                    f'Para este monto puedes seleccionar '
                    f'entre 1 y {maximo} cuotas.'
                )

            else:

                # =========================
                # CALCULAR SCORE
                # =========================

                resultado = calcular_score_simulador(
                    ingresos,
                    gastos
                )

                context.update(resultado)

                print("RESULTADO DEL SCORE:", resultado)

                # =========================
                # DATOS DEL CRÉDITO
                # =========================

                context['monto'] = monto
                context['plazo'] = plazo

                # =========================
                # CALCULAR CUOTA
                # =========================

                if resultado['tasa_interes'] is not None:

                    tabla = calcular_tabla_amortizacion(
                        monto,
                        resultado['tasa_interes'],
                        plazo
                    )

                    total_intereses = sum(
                        fila['interes']
                        for fila in tabla
                    )

                    total_pagar = (
                        monto + total_intereses
                    )

                    cuota_mensual = (
                        tabla[0]['valor_cuota']
                        if tabla
                        else Decimal('0')
                    )

                    context['tabla'] = tabla

                    context['total_intereses'] = (
                        total_intereses
                    )

                    context['total_pagar'] = (
                        total_pagar
                    )

                    context['cuota_mensual'] = (
                        cuota_mensual
                    )

                    # =========================
                    # COMPROBAR CAPACIDAD
                    # =========================

                    saldo_disponible = (
                        resultado['saldo_disponible']
                    )

                    context['cuota_permitida'] = (
                        saldo_disponible
                    )

                    context['puede_pagar_cuota'] = (
                        cuota_mensual <= saldo_disponible
                    )

        except (ValueError, TypeError, ArithmeticError):

            context['error'] = (
                'Verifica que todos los valores '
                'ingresados sean válidos.'
            )

    return render(
        request,
        'loans/simulador_publico.html',
        context
    )


@require_POST
@cliente_required
def calcular_simulacion_ajax(request):

    """Endpoint HTMX para cálculo en tiempo real."""

    try:

        monto_texto = request.POST.get('monto', '').strip()

        if not monto_texto.isascii() or not monto_texto.isdigit():
            return render(
                request,
                'loans/partials/error_simulacion.html',
                {
                    'mensaje': 'Ingresa un monto válido utilizando solo números.'
                }
            )

        monto = Decimal(monto_texto)

        plazo_texto = request.POST.get('plazo', '').strip()

        if not plazo_texto.isascii() or not plazo_texto.isdigit():

            return render(
                request,
                'loans/partials/error_simulacion.html',
                {
                    'mensaje': 'Selecciona un número de cuotas válido.'
                }
            )

        plazo = int(plazo_texto)

        maximo_cuotas = obtener_maximo_cuotas(monto)

        if maximo_cuotas == 0:

            return render(
                request,
                'loans/partials/error_simulacion.html',
                {
                    'mensaje': (
                        'El monto del crédito debe estar '
                        'entre $100.000 y $1.000.000.'
                    )
                }
            )

        if plazo < 1 or plazo > maximo_cuotas:

            return render(
                request,
                'loans/partials/error_simulacion.html',
                {
                    'mensaje': (
                        f'Para un crédito de este monto puedes '
                        f'seleccionar entre 1 y {maximo_cuotas} cuotas.'
                    )
                }
            )
        # ======================================================
        # SOLICITUD TEMPORAL PARA CALCULAR EL SCORE REAL
        # ======================================================

        solicitud_simulada = SimpleNamespace(
            monto_solicitado=monto,
            plazo_meses=plazo
        )

        # El score utiliza:
        # - Antigüedad real del usuario
        # - Historial real de préstamos
        # - Ingresos y gastos reales
        # - Monto y plazo del simulador

        score, nivel_riesgo, tasa_interes = (
            calcular_score_deterministico(
                request.user,
                solicitud_simulada
            )
        )

        if tasa_interes is None:

            return render(
                request,
                'loans/partials/error_simulacion.html',
                {
                    'mensaje': (
                        'Lo sentimos, tu perfil no cumple '
                        'con los requisitos mínimos para '
                        'este crédito.'
                    )
                }
            )

        # ======================================================
        # TABLA DE AMORTIZACIÓN
        # ======================================================

        tabla = calcular_tabla_amortizacion(
            monto,
            tasa_interes,
            plazo
        )

        total_intereses = sum(
            fila['interes']
            for fila in tabla
        )

        total_pagar = monto + total_intereses

        context = {

            'monto': monto,

            'plazo': plazo,

            'score': score,

            'nivel_riesgo': nivel_riesgo,

            'tasa_interes': tasa_interes,

            'tabla': tabla,

            'total_intereses': total_intereses,

            'total_pagar': total_pagar,

            'cuota_mensual': (
                tabla[0]['valor_cuota']
                if tabla
                else 0
            ),

        }

        return render(
            request,
            'loans/partials/resultado_simulacion.html',
            context
        )

    except Exception:

        return render(
            request,
            'loans/partials/error_simulacion.html',
            {
                'mensaje': (
                    'Ocurrió un error al calcular la simulación. '
                    'Inténtalo nuevamente.'
                )
            },
            status=500
        )

@login_required
def documento_pago_view(request, pago_id):

    pago = get_object_or_404(
        Pago,
        id=pago_id
    )

    # Solo el propietario o un administrador.
    if (
        pago.cliente_id != request.user.id
        and request.user.role != 'administrador'
    ):
        raise Http404("Comprobante no encontrado.")

    if not pago.comprobante:
        raise Http404("Comprobante no disponible.")

    try:
        pago.comprobante.open('rb')
    except (OSError, ValueError):
        raise Http404("Comprobante no disponible.")

    respuesta = FileResponse(
        pago.comprobante,
        as_attachment=False
    )

    respuesta['X-Content-Type-Options'] = 'nosniff'
    respuesta['Cache-Control'] = 'private, no-store'

    return respuesta