
from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def pesos(valor):
    if valor is None or valor == "":
        return "$0"

    try:
        valor = Decimal(str(valor))

        # Mantener dos decimales para los valores que los necesiten.
        numero = f"{abs(valor):.2f}"
        parte_entera, parte_decimal = numero.split(".")

        # Agregar puntos como separadores de miles.
        grupos = []
        while parte_entera:
            grupos.insert(0, parte_entera[-3:])
            parte_entera = parte_entera[:-3]

        entero_formateado = ".".join(grupos) or "0"

        # Mostrar decimales solo cuando sean distintos de cero.
        signo = "-" if valor < 0 else ""

        if parte_decimal == "00":
            return f"{signo}${entero_formateado}"

        return f"{signo}${entero_formateado},{parte_decimal}"

    except (ValueError, TypeError, InvalidOperation, ArithmeticError):
        return valor
