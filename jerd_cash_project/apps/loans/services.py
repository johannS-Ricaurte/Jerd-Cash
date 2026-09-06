# apps/loans/services.py
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from dateutil.relativedelta import relativedelta
from .models import Prestamo, Cuota
from django.conf import settings

def calcular_score_deterministico(cliente):
    """
    Calcula el Score (0-1000) basado en 3 variables ponderadas.
    """
    # 1. Antigüedad (30%)
    meses_antiguedad = (date.today() - cliente.date_joined.date()).days // 30
    if meses_antiguedad >= 12: score_ant = 100
    elif meses_antiguedad >= 6: score_ant = 70
    elif meses_antiguedad >= 3: score_ant = 40
    else: score_ant = 20
    
    # 2. Historial de cumplimiento (40%)
    prestamos_anteriores = Prestamo.objects.filter(cliente=cliente, estado__in=['pagado', 'desembolsado'])
    if prestamos_anteriores.exists():
        cuotas_totales = Cuota.objects.filter(prestamo__in=prestamos_anteriores).count()
        cuotas_pagadas = Cuota.objects.filter(prestamo__in=prestamos_anteriores, pagada=True).count()
        pct_cumplimiento = (cuotas_pagadas / cuotas_totales * 100) if cuotas_totales > 0 else 100
    else:
        pct_cumplimiento = 80 # Cliente nuevo, score neutro
    score_cumplimiento = min(pct_cumplimiento, 100)
    
    # 3. Capacidad de endeudamiento (30%)
    # NOTA PROTOTIPO: Asumimos ingresos de $2.000.000. En producción, esto viene del modelo CustomUser.
    ingresos_estimados = Decimal('2000000')
    ratio_endeudamiento = 30 # Asumimos un 30% para el prototipo
    if ratio_endeudamiento <= 20: score_cap = 100
    elif ratio_endeudamiento <= 30: score_cap = 70
    elif ratio_endeudamiento <= 40: score_cap = 40
    else: score_cap = 10
    
    # Cálculo final ponderado y escalado a 1000
    score_final = int((score_ant * 0.30) + (score_cumplimiento * 0.40) + (score_cap * 0.30)) * 10
    
    # Reglas de negocio para tasa de interés
    if score_final >= 800:
        return score_final, 'Bajo', Decimal('1.5')
    elif score_final >= 600:
        return score_final, 'Medio', Decimal('2.0')
    elif score_final >= 400:
        return score_final, 'Alto', Decimal('2.5')
    else:
        return score_final, 'Muy Alto', None # Rechazo automático


def calcular_tabla_amortizacion(monto, tasa_mensual, plazo_meses, fecha_inicio=None):
    """
    Implementación exacta de las fórmulas del Anexo A del anteproyecto.
    """
    if fecha_inicio is None:
        fecha_inicio = date.today()
    
    i = tasa_mensual / Decimal('100') # Convertir porcentaje a decimal
    n = plazo_meses
    P = monto
    
    # Fórmula: C = P * [i(1+i)^n] / [(1+i)^n - 1]
    if i == 0:
        cuota = P / n
    else:
        cuota = P * (i * (1 + i)**n) / ((1 + i)**n - 1)
    
    cuota = cuota.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    tabla = []
    saldo = P
    
    for mes in range(1, n + 1):
        interes = (saldo * i).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        abono_capital = (cuota - interes).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        saldo = saldo - abono_capital
        fecha_vencimiento = fecha_inicio + relativedelta(months=mes)
        
        tabla.append({
            'numero_cuota': mes,
            'fecha_vencimiento': fecha_vencimiento,
            'valor_cuota': cuota,
            'interes': interes,
            'abono_capital': abono_capital,
            'saldo_pendiente': max(saldo, Decimal('0'))
        })
    
    return tabla