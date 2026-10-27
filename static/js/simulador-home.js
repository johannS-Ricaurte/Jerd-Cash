
(function () {
    "use strict";

    function plazoMaximo(monto) {
        if (monto < 200000) return 1;
        if (monto < 300000) return 2;
        if (monto < 400000) return 3;
        if (monto < 500000) return 4;
        if (monto < 600000) return 5;
        if (monto < 700000) return 6;
        if (monto < 800000) return 7;
        if (monto < 900000) return 8;
        if (monto < 1000000) return 10;
        return 12;
    }

    function validarDatos(ingresos, gastos, monto, plazo) {
        if (![ingresos, gastos, monto, plazo].every(Number.isFinite)) {
            throw new Error("Verifica que todos los valores ingresados sean válidos.");
        }

        if (!Number.isInteger(ingresos) ||
            !Number.isInteger(gastos) ||
            !Number.isInteger(monto) ||
            !Number.isInteger(plazo)) {
            throw new Error("Ingresa valores enteros válidos.");
        }

        if (ingresos <= 0) {
            throw new Error("Los ingresos mensuales deben ser mayores a $0.");
        }

        if (gastos < 0) {
            throw new Error("Los gastos mensuales no pueden ser negativos.");
        }

        if (gastos > ingresos) {
            throw new Error("Los gastos mensuales no pueden ser mayores que los ingresos.");
        }

        if (monto < 100000) {
            throw new Error("El monto mínimo del crédito es $100.000.");
        }

        if (monto > 1000000) {
            throw new Error("El monto máximo del crédito es $1.000.000.");
        }

        if (plazo < 1 || plazo > plazoMaximo(monto)) {
            throw new Error("El plazo seleccionado no es válido para el monto solicitado.");
        }
    }

    // División con redondeo HALF_UP para cantidades positivas.
    function dividirRedondeando(numerador, denominador) {
        return (numerador * 2n + denominador) / (denominador * 2n);
    }

    function calcularAmortizacion(monto, tasa, plazo) {
        const principal = BigInt(monto) * 100n;
        const tasaNumerador = BigInt(Math.round(tasa * 10));
        const tasaDenominador = 1000n;

        const base = tasaDenominador + tasaNumerador;
        const potencia = base ** BigInt(plazo);
        const denominadorPotencia = tasaDenominador ** BigInt(plazo);

        const cuotaCentavos = dividirRedondeando(
            principal * tasaNumerador * potencia,
            tasaDenominador * (potencia - denominadorPotencia)
        );

        let saldo = principal;
        let intereses = 0n;
        const tabla = [];

        for (let mes = 1; mes <= plazo; mes++) {
            const interes = dividirRedondeando(
                saldo * tasaNumerador,
                tasaDenominador
            );

            const capital = cuotaCentavos - interes;
            saldo -= capital;
            intereses += interes;

            tabla.push({
                numero_cuota: mes,
                valor_cuota: Number(cuotaCentavos) / 100,
                interes: Number(interes) / 100,
                abono_capital: Number(capital) / 100,
                saldo_pendiente: Number(saldo > 0n ? saldo : 0n) / 100
            });
        }

        return {
            tabla,
            cuota_mensual: Number(cuotaCentavos) / 100,
            total_intereses: Number(intereses) / 100,
            total_pagar: monto + Number(intereses) / 100
        };
    }

    function calcularSimulacion(ingresos, gastos, monto, plazo) {
        validarDatos(ingresos, gastos, monto, plazo);

        const saldoDisponible = ingresos - gastos;
        const score = Math.max(
            0,
            Math.min(
                1000,
                Number(
                    (BigInt(saldoDisponible) * 1000n) /
                    BigInt(ingresos)
                )
            )
        );

        const capacidadPago = (saldoDisponible / ingresos) * 100;

        let nivelRiesgo;
        let tasaInteres;

        if (score >= 800) {
            nivelRiesgo = "Bajo";
            tasaInteres = 1.5;
        } else if (score >= 600) {
            nivelRiesgo = "Medio";
            tasaInteres = 2.0;
        } else if (score >= 400) {
            nivelRiesgo = "Alto";
            tasaInteres = 2.5;
        } else {
            nivelRiesgo = "Muy Alto";
            tasaInteres = null;
        }

        const resultado = {
            ingresos,
            gastos,
            monto,
            plazo,
            score,
            nivel_riesgo: nivelRiesgo,
            tasa_interes: tasaInteres,
            saldo_disponible: saldoDisponible,
            capacidad_pago: capacidadPago
        };

        if (tasaInteres !== null) {
            const amortizacion = calcularAmortizacion(
                monto,
                tasaInteres,
                plazo
            );

            Object.assign(resultado, amortizacion);

            resultado.puede_pagar_cuota =
                amortizacion.cuota_mensual <= saldoDisponible;
        }

        return resultado;
    }

        // ==========================================
    // MOSTRAR RESULTADOS OFFLINE
    // ==========================================

    function mostrarResultadoOffline(resultado) {
        const contenedor = document.getElementById(
            "resultado-simulador-offline"
        );

        if (!contenedor) return;

        const pesos = (valor) =>
            new Intl.NumberFormat("es-CO", {
                style: "currency",
                currency: "COP",
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(valor);

        const porcentaje = (valor) =>
            new Intl.NumberFormat("es-CO", {
                minimumFractionDigits: 1,
                maximumFractionDigits: 1
            }).format(valor);

        const tieneTasa = resultado.tasa_interes !== null;

        const condiciones = tieneTasa
            ? `
                <div class="grid grid-cols-2 gap-3 mt-4">
                    <div class="p-4 bg-white border border-gray-200 rounded-xl text-center">
                        <p class="text-xs text-gray-500">Tasa mensual</p>
                        <p class="mt-1 text-2xl font-bold text-blue-700">
                            ${resultado.tasa_interes}%
                        </p>
                    </div>

                    <div class="p-4 bg-white border border-gray-200 rounded-xl text-center">
                        <p class="text-xs text-gray-500">Cuota mensual</p>
                        <p class="mt-1 text-xl font-bold text-green-700">
                            ${pesos(resultado.cuota_mensual)}
                        </p>
                    </div>
                </div>

                <div class="mt-5 space-y-3">
                    <div class="flex justify-between border-b pb-3">
                        <span class="text-gray-500">Monto solicitado</span>
                        <span class="font-semibold">${pesos(resultado.monto)}</span>
                    </div>

                    <div class="flex justify-between border-b pb-3">
                        <span class="text-gray-500">Plazo</span>
                        <span class="font-semibold">${resultado.plazo} meses</span>
                    </div>
                </div>

                <div class="mt-6 p-5 rounded-xl border ${
                    resultado.puede_pagar_cuota
                        ? "bg-green-50 border-green-200"
                        : "bg-yellow-50 border-yellow-200"
                }">
                    <p class="font-bold ${
                        resultado.puede_pagar_cuota
                            ? "text-green-800"
                            : "text-yellow-800"
                    }">
                        ${
                            resultado.puede_pagar_cuota
                                ? "✓ La cuota está dentro de tu capacidad de pago"
                                : "La cuota supera tu capacidad disponible"
                        }
                    </p>
                    <p class="mt-2 text-sm">
                        Saldo disponible: ${pesos(resultado.saldo_disponible)}
                    </p>
                </div>
            `
            : `
                <div class="mt-5 p-4 bg-yellow-50 border border-yellow-200 rounded-xl">
                    <p class="font-semibold text-yellow-800">
                        No hay una tasa disponible para este nivel de riesgo.
                    </p>
                </div>
            `;

        contenedor.innerHTML = `
            <h4 class="text-xl font-bold text-blue-950 text-center">
                Resultado de tu simulación
            </h4>

            <p class="mt-2 text-center text-xs text-gray-500">
                Simulación realizada sin conexión a internet.
            </p>

            <div class="mt-5 space-y-3">
                <div class="flex justify-between border-b pb-3">
                    <span class="text-gray-500">Ingresos</span>
                    <span class="font-semibold">${pesos(resultado.ingresos)}</span>
                </div>

                <div class="flex justify-between border-b pb-3">
                    <span class="text-gray-500">Gastos</span>
                    <span class="font-semibold">${pesos(resultado.gastos)}</span>
                </div>

                <div class="flex justify-between border-b pb-3">
                    <span class="text-gray-500">Saldo disponible</span>
                    <span class="font-semibold text-green-700">
                        ${pesos(resultado.saldo_disponible)}
                    </span>
                </div>
            </div>

            <div class="mt-6 p-5 bg-blue-50 border border-blue-100 rounded-xl">
                <div class="text-center">
                    <p class="text-sm text-gray-500">Puntaje estimado</p>
                    <p class="mt-1 text-5xl font-bold text-blue-900">
                        ${resultado.score}
                        <span class="text-lg text-gray-500">/ 1000</span>
                    </p>
                    <p class="mt-2 text-sm text-gray-600">
                        Nivel de riesgo:
                        <strong class="text-blue-900">
                            ${resultado.nivel_riesgo}
                        </strong>
                    </p>
                </div>
            </div>

            <div class="mt-4 p-4 rounded-lg bg-gray-50 text-center">
                <p class="text-sm text-gray-500">Capacidad de pago</p>
                <p class="text-xl font-bold text-gray-900">
                    ${porcentaje(resultado.capacidad_pago)}%
                </p>
            </div>

            ${condiciones}
        `;

        contenedor.classList.remove("hidden");

        const resultadoDjango = document.getElementById(
            "resultado-simulador-django"
        );

        if (resultadoDjango) {
            resultadoDjango.classList.add("hidden");
        }
    }

    // ==========================================
    // CONTROLAR EL FORMULARIO
    // ==========================================

    document.addEventListener("DOMContentLoaded", function () {
        const formulario = document.getElementById("simulador-form");

        if (!formulario) return;

        formulario.addEventListener("submit", function (evento) {

            // Evitar siempre el envío del formulario a Django.
            evento.preventDefault();

            const contenedor = document.getElementById(
                "resultado-simulador-offline"
            );

            try {
                const obtenerNumero = (id) => {
                    const campo = document.getElementById(id);
                    const valor = campo.value.replace(/\D/g, "");
                    return valor === "" ? NaN : Number(valor);
                };

                const resultado = calcularSimulacion(
                    obtenerNumero("ingresos"),
                    obtenerNumero("gastos"),
                    obtenerNumero("monto"),
                    obtenerNumero("plazo")
                );

                mostrarResultadoOffline(resultado);

            } catch (error) {
                if (contenedor) {
                    contenedor.textContent = error.message;
                    contenedor.classList.remove("hidden");
                    contenedor.classList.add(
                        "p-4",
                        "rounded-lg",
                        "bg-red-50",
                        "text-red-700"
                    );
                }
            }
        });
    });

    // Mantener disponibles las funciones de cálculo.
    window.JERDCashSimuladorHome = {
        calcularSimulacion,
        plazoMaximo
    };
})();
