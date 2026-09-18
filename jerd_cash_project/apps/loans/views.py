# apps/loans/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from decimal import Decimal
from .services import calcular_tabla_amortizacion, calcular_score_deterministico, calcular_score_simulador

@login_required
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
                request.POST.get(
                    'ingresos',
                    '0'
                )
            )

            gastos = Decimal(
                request.POST.get(
                    'gastos',
                    '0'
                )
            )

            monto = Decimal(
                request.POST.get(
                    'monto',
                    '0'
                )
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

            elif monto < 100000:

                context['error'] = (
                    'El monto mínimo del crédito es '
                    '$100.000.'
                )

            elif plazo not in [3, 6, 12, 24, 36]:

                context['error'] = (
                    'Selecciona un plazo válido entre '
                    '3 y 36 meses.'
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
@login_required
def calcular_simulacion_ajax(request):
    """Endpoint HTMX para cálculo en tiempo real."""
    try:
        monto = Decimal(request.POST.get('monto', '0'))
        plazo = int(request.POST.get('plazo', '0'))
        
        if monto < 100000 or plazo < 1 or plazo > 36:
            return render(request, 'loans/partials/error_simulacion.html', {
                'mensaje': 'Monto mínimo: $100.000 | Plazo: 1 a 36 meses'
            })
        
        score, nivel_riesgo, tasa_interes = calcular_score_deterministico(request.user)
        
        if tasa_interes is None:
            return render(request, 'loans/partials/error_simulacion.html', {
                'mensaje': 'Lo sentimos, tu perfil no cumple con los requisitos mínimos para este crédito.'
            })
        
        tabla = calcular_tabla_amortizacion(monto, tasa_interes, plazo)
        total_intereses = sum(fila['interes'] for fila in tabla)
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
            'cuota_mensual': tabla[0]['valor_cuota'] if tabla else 0,
        }
        return render(request, 'loans/partials/resultado_simulacion.html', context)
        
    except Exception as e:
        return render(request, 'loans/partials/error_simulacion.html', {'mensaje': f'Error: {str(e)}'})