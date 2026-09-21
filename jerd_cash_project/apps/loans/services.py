# apps/loans/services.py
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from dateutil.relativedelta import relativedelta
from .models import Prestamo, Cuota
from django.conf import settings


def calcular_score_deterministico(cliente, solicitud=None):
        
        """
        Calcula el Score (0-1000) basado en 4 variables:

        1. Antigüedad del cliente              -> 20%
        2. Historial de cumplimiento           -> 30%
        3. Gastos frente a ingresos            -> 20%
        4. Capacidad para asumir nuevo crédito -> 30%

        La capacidad del nuevo crédito utiliza
        una tasa de referencia del 2% mensual
        para evitar una dependencia circular
        entre score, tasa y cuota.
        """

        # ==========================================================
        # 1. ANTIGÜEDAD DEL CLIENTE
        # ==========================================================

        meses_antiguedad = (
            date.today() - cliente.date_joined.date()
        ).days // 30

        if meses_antiguedad >= 12:
            score_ant = 100
        elif meses_antiguedad >= 6:
            score_ant = 70
        elif meses_antiguedad >= 3:
            score_ant = 40
        else:
            score_ant = 20

        # ==========================================================
        # 2. HISTORIAL DE CUMPLIMIENTO
        # ==========================================================

        prestamos_anteriores = Prestamo.objects.filter(
            cliente=cliente,
            estado__in=['pagado', 'desembolsado']
        )

        if prestamos_anteriores.exists():

            cuotas_totales = Cuota.objects.filter(
                prestamo__in=prestamos_anteriores
            ).count()

            cuotas_pagadas = Cuota.objects.filter(
                prestamo__in=prestamos_anteriores,
                pagada=True
            ).count()

            pct_cumplimiento = (
                cuotas_pagadas / cuotas_totales * 100
            ) if cuotas_totales > 0 else 100

        else:
            # Cliente sin historial:
            # se utiliza un valor de referencia neutral.
            pct_cumplimiento = 80

        score_cumplimiento = min(
            pct_cumplimiento,
            100
        )

        # ==========================================================
        # 3. GASTOS FRENTE A INGRESOS
        # ==========================================================

        try:
            perfil = cliente.perfil_cliente

            ingresos_mensuales = perfil.ingresos_mensuales
            gastos_mensuales = perfil.gastos_mensuales

        except Exception:
            ingresos_mensuales = Decimal('0')
            gastos_mensuales = Decimal('0')

        if ingresos_mensuales > 0:

            ratio_gastos = (
                gastos_mensuales / ingresos_mensuales
            ) * 100

        else:
            ratio_gastos = Decimal('100')

        if ratio_gastos <= 20:
            score_gastos = 100

        elif ratio_gastos <= 30:
            score_gastos = 70

        elif ratio_gastos <= 40:
            score_gastos = 40

        else:
            score_gastos = 10

        # ==========================================================
        # 4. CAPACIDAD PARA ASUMIR EL NUEVO CRÉDITO
        # ==========================================================

        score_capacidad_nuevo = 50
        cuota_estimada = Decimal('0')
        disponible_despues_cuota = (
            ingresos_mensuales - gastos_mensuales
        )

        if solicitud is not None and ingresos_mensuales > 0:

            monto = solicitud.monto_solicitado
            plazo = solicitud.plazo_meses

            # Tasa de referencia utilizada solamente
            # para evaluar la capacidad de pago.
            tasa_referencia = Decimal('2.0')

            i = tasa_referencia / Decimal('100')
            n = plazo

            if i == 0:

                cuota_estimada = (
                    monto / n
                )

            else:

                cuota_estimada = (
                    monto
                    * (i * (1 + i) ** n)
                    / ((1 + i) ** n - 1)
                )

            cuota_estimada = cuota_estimada.quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP
            )

            disponible_despues_cuota = (
                ingresos_mensuales
                - gastos_mensuales
                - cuota_estimada
            )

            # Porcentaje de los ingresos disponibles
            # que representa la nueva cuota.
            ingreso_disponible = (
                ingresos_mensuales - gastos_mensuales
            )

            if ingreso_disponible > 0:

                porcentaje_cuota_disponible = (
                    cuota_estimada / ingreso_disponible
                ) * 100

            else:

                porcentaje_cuota_disponible = Decimal('100')

            if porcentaje_cuota_disponible <= 20:

                score_capacidad_nuevo = 100

            elif porcentaje_cuota_disponible <= 30:

                score_capacidad_nuevo = 70

            elif porcentaje_cuota_disponible <= 40:

                score_capacidad_nuevo = 40

            else:

                score_capacidad_nuevo = 10

        # ==========================================================
        # 5. SCORE FINAL
        # ==========================================================

        score_final = int(
            (score_ant * 0.20)
            + (score_cumplimiento * 0.30)
            + (score_gastos * 0.20)
            + (score_capacidad_nuevo * 0.30)
        ) * 10

        # ==========================================================
        # 6. NIVEL DE RIESGO Y TASA
        # ==========================================================

        if score_final >= 800:

            nivel_riesgo = 'Bajo'
            tasa_interes = Decimal('1.5')

        elif score_final >= 600:

            nivel_riesgo = 'Medio'
            tasa_interes = Decimal('2.0')

        elif score_final >= 400:

            nivel_riesgo = 'Alto'
            tasa_interes = Decimal('2.5')

        else:

            nivel_riesgo = 'Muy Alto'
            tasa_interes = None

        return score_final, nivel_riesgo, tasa_interes



def calcular_detalle_score(cliente, solicitud=None):
        """
        Calcula y devuelve el detalle utilizado para construir
        el score determinístico del cliente.

        Los factores son:

        1. Antigüedad                 -> 20%
        2. Historial de cumplimiento  -> 30%
        3. Gastos / ingresos          -> 20%
        4. Capacidad nuevo crédito    -> 30%
        """

        # ==========================================================
        # 1. ANTIGÜEDAD
        # ==========================================================

        meses_antiguedad = (
            date.today() - cliente.date_joined.date()
        ).days // 30

        if meses_antiguedad >= 12:
            score_ant = 100
        elif meses_antiguedad >= 6:
            score_ant = 70
        elif meses_antiguedad >= 3:
            score_ant = 40
        else:
            score_ant = 20

        # ==========================================================
        # 2. HISTORIAL
        # ==========================================================

        prestamos_anteriores = Prestamo.objects.filter(
            cliente=cliente,
            estado__in=['pagado', 'desembolsado']
        )

        if prestamos_anteriores.exists():

            cuotas_totales = Cuota.objects.filter(
                prestamo__in=prestamos_anteriores
            ).count()

            cuotas_pagadas = Cuota.objects.filter(
                prestamo__in=prestamos_anteriores,
                pagada=True
            ).count()

            pct_cumplimiento = (
                cuotas_pagadas / cuotas_totales * 100
            ) if cuotas_totales > 0 else 100

        else:

            cuotas_totales = 0
            cuotas_pagadas = 0

            # Cliente sin historial.
            # Es un valor de referencia, no un porcentaje
            # real de cuotas pagadas.
            pct_cumplimiento = 80

        score_cumplimiento = min(
            pct_cumplimiento,
            100
        )

        # ==========================================================
        # 3. GASTOS FRENTE A INGRESOS
        # ==========================================================

        try:

            perfil = cliente.perfil_cliente

            ingresos_mensuales = perfil.ingresos_mensuales
            gastos_mensuales = perfil.gastos_mensuales

        except Exception:

            ingresos_mensuales = Decimal('0')
            gastos_mensuales = Decimal('0')

        if ingresos_mensuales > 0:

            ratio_gastos = (
                gastos_mensuales / ingresos_mensuales
            ) * 100

        else:

            ratio_gastos = Decimal('100')

        if ratio_gastos <= 20:

            score_gastos = 100

        elif ratio_gastos <= 30:

            score_gastos = 70

        elif ratio_gastos <= 40:

            score_gastos = 40

        else:

            score_gastos = 10

        # ==========================================================
        # 4. CAPACIDAD PARA EL NUEVO CRÉDITO
        # ==========================================================

        cuota_estimada = Decimal('0')

        disponible_actual = (
            ingresos_mensuales
            - gastos_mensuales
        )

        disponible_despues_cuota = disponible_actual

        porcentaje_cuota_disponible = Decimal('100')

        score_capacidad_nuevo = 50

        tasa_referencia = Decimal('2.0')

        if solicitud is not None and ingresos_mensuales > 0:

            monto = solicitud.monto_solicitado
            plazo = solicitud.plazo_meses

            i = tasa_referencia / Decimal('100')
            n = plazo

            if i == 0:

                cuota_estimada = (
                    monto / n
                )

            else:

                cuota_estimada = (
                    monto
                    * (i * (1 + i) ** n)
                    / ((1 + i) ** n - 1)
                )

            cuota_estimada = cuota_estimada.quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP
            )

            disponible_despues_cuota = (
                ingresos_mensuales
                - gastos_mensuales
                - cuota_estimada
            )

            if disponible_actual > 0:

                porcentaje_cuota_disponible = (
                    cuota_estimada / disponible_actual
                ) * 100

            else:

                porcentaje_cuota_disponible = Decimal('100')

            if porcentaje_cuota_disponible <= 20:

                score_capacidad_nuevo = 100

            elif porcentaje_cuota_disponible <= 30:

                score_capacidad_nuevo = 70

            elif porcentaje_cuota_disponible <= 40:

                score_capacidad_nuevo = 40

            else:

                score_capacidad_nuevo = 10

        # ==========================================================
        # 5. SCORE FINAL
        # ==========================================================

        score_final = int(
            (score_ant * 0.20)
            + (score_cumplimiento * 0.30)
            + (score_gastos * 0.20)
            + (score_capacidad_nuevo * 0.30)
        ) * 10

        # ==========================================================
        # 6. NIVEL DE RIESGO
        # ==========================================================

        if score_final >= 800:

            nivel_riesgo = 'Bajo'
            tasa_interes = Decimal('1.5')

        elif score_final >= 600:

            nivel_riesgo = 'Medio'
            tasa_interes = Decimal('2.0')

        elif score_final >= 400:

            nivel_riesgo = 'Alto'
            tasa_interes = Decimal('2.5')

        else:

            nivel_riesgo = 'Muy Alto'
            tasa_interes = None

        # ==========================================================
        # 7. RESULTADO DETALLADO
        # ==========================================================

        return {
            'score_final': score_final,
            'nivel_riesgo': nivel_riesgo,
            'tasa_interes': tasa_interes,

            'meses_antiguedad': meses_antiguedad,
            'score_antiguedad': score_ant,

            'cuotas_totales': cuotas_totales,
            'cuotas_pagadas': cuotas_pagadas,
            'porcentaje_cumplimiento': round(
                pct_cumplimiento,
                2
            ),
            'score_cumplimiento': round(
                score_cumplimiento,
                2
            ),

            'ingresos_mensuales': ingresos_mensuales,
            'gastos_mensuales': gastos_mensuales,

            'ratio_gastos': round(
                ratio_gastos,
                2
            ),
            'score_gastos': score_gastos,

            'monto_solicitado': (
                solicitud.monto_solicitado
                if solicitud is not None
                else Decimal('0')
            ),

            'plazo_meses': (
                solicitud.plazo_meses
                if solicitud is not None
                else 0
            ),

            'tasa_referencia': tasa_referencia,

            'cuota_estimada': cuota_estimada,

            'disponible_actual': disponible_actual,

            'disponible_despues_cuota': (
                disponible_despues_cuota
            ),

            'porcentaje_cuota_disponible': round(
                porcentaje_cuota_disponible,
                2
            ),

            'score_capacidad_nuevo': (
                score_capacidad_nuevo
            ),
        }


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

def calcular_score_simulador(ingresos, gastos):
    """
    Calcula un puntaje ficticio de 0 a 1000 para el
    simulador público de crédito.

    El puntaje se basa en la capacidad de pago:
    
        saldo_disponible = ingresos - gastos
        capacidad = saldo_disponible / ingresos
        score = capacidad * 1000
    """

    ingresos = Decimal(ingresos)
    gastos = Decimal(gastos)

    # Validación básica
    if ingresos <= 0:
        return {
            'score': 0,
            'nivel_riesgo': 'Muy Alto',
            'tasa_interes': None,
            'saldo_disponible': Decimal('0'),
            'capacidad_pago': Decimal('0'),
        }

    # Saldo disponible después de los gastos
    saldo_disponible = ingresos - gastos

    # Si los gastos superan los ingresos,
    # la capacidad disponible será 0.
    if saldo_disponible < 0:
        saldo_disponible = Decimal('0')

    # Porcentaje de capacidad de pago
    capacidad_pago = (
        saldo_disponible / ingresos
    ) * Decimal('100')

    # Puntaje de 0 a 1000
    score = int(
        (capacidad_pago * Decimal('10'))
    )

    # Limitar el puntaje entre 0 y 1000
    score = max(0, min(score, 1000))

    # Rangos y tasas existentes de JERD-Cash
    if score >= 800:

        nivel_riesgo = 'Bajo'
        tasa_interes = Decimal('1.5')

    elif score >= 600:

        nivel_riesgo = 'Medio'
        tasa_interes = Decimal('2.0')

    elif score >= 400:

        nivel_riesgo = 'Alto'
        tasa_interes = Decimal('2.5')

    else:

        nivel_riesgo = 'Muy Alto'
        tasa_interes = None

    return {
        'score': score,
        'nivel_riesgo': nivel_riesgo,
        'tasa_interes': tasa_interes,
        'saldo_disponible': saldo_disponible,
        'capacidad_pago': capacidad_pago,
    }

