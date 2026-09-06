# apps/loans/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from decimal import Decimal
from .services import calcular_tabla_amortizacion, calcular_score_deterministico

@login_required
def simulador_view(request):
    return render(request, 'loans/simulador.html', {'titulo': 'Simulador de Crédito'})

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