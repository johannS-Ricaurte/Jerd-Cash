from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
import secrets
from decimal import Decimal

from jerd_cash_project.apps.loans.services import (
    calcular_tabla_amortizacion,
    calcular_score_simulador,
)

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .services import registrar_usuario_con_consentimiento
from .models import CustomUser, ConsentimientoLegal

from jerd_cash_project.apps.cliente.models import PerfilCliente


def home_view(request):

    context = {}

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

            # Validaciones

            if ingresos <= 0:

                context['error'] = (
                    'Los ingresos mensuales deben '
                    'ser mayores a $0.'
                )

            elif gastos < 0:

                context['error'] = (
                    'Los gastos mensuales no pueden '
                    'ser negativos.'
                )

            elif gastos > ingresos:

                context['error'] = (
                    'Los gastos mensuales no pueden '
                    'ser mayores que los ingresos.'
                )

            elif monto < 100000:

                context['error'] = (
                    'El monto mínimo del crédito es '
                    '$100.000.'
                )

            elif plazo not in [3, 6, 12, 24, 36]:

                context['error'] = (
                    'Selecciona un plazo válido.'
                )

            else:

                resultado = calcular_score_simulador(
                    ingresos,
                    gastos
                )

                context.update(resultado)

                context['ingresos'] = ingresos
                context['gastos'] = gastos
                context['monto'] = monto
                context['plazo'] = plazo

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

                    saldo_disponible = (
                        resultado['saldo_disponible']
                    )

                    context['cuota_permitida'] = (
                        saldo_disponible
                    )

                    context['puede_pagar_cuota'] = (
                        cuota_mensual <= saldo_disponible
                    )

        except (
            ValueError,
            TypeError,
            ArithmeticError
        ):

            context['error'] = (
                'Verifica que todos los valores '
                'ingresados sean válidos.'
            )

    return render(
        request,
        'users/home.html',
        context
    )



def registro_view(request):
    """
    Vista para manejar el registro de nuevos clientes.
    """

    if request.method == 'POST':

        first_name = request.POST.get('first_name', '').strip()
        primer_apellido = request.POST.get(
            'primer_apellido',
            ''
        ).strip()

        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        cedula = request.POST.get('cedula', '').strip()

        acepta_terminos = 'acepta_terminos' in request.POST

        x_forwarded_for = request.META.get(
            'HTTP_X_FORWARDED_FOR'
        )

        ip_address = (
            x_forwarded_for.split(',')[0].strip()
            if x_forwarded_for
            else request.META.get('REMOTE_ADDR')
        )

        try:

            registrar_usuario_con_consentimiento(
                first_name=first_name,
                primer_apellido=primer_apellido,
                username=username,
                email=email,
                password=password,
                cedula=cedula,
                ip_address=ip_address,
                acepta_terminos=acepta_terminos
            )

            messages.success(
                request,
                "Registro exitoso. Bienvenido a JERD-Cash."
            )

            return redirect('login')

        except ValidationError as e:

            messages.error(
                request,
                str(e)
            )

        except Exception:

            messages.error(
                request,
                "Ocurrió un error durante el registro. "
                "Verifique los datos."
            )

    return render(
        request,
        'users/register.html'
    )


def login_view(request):
    """
    Inicio de sesión tradicional con usuario y contraseña.
    """

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        usuario = authenticate(
            request,
            username=username,
            password=password
        )

        if usuario is not None:

            login(request, usuario)

            messages.success(
                request,
                f"Bienvenido, {usuario.username}."
            )

            return redirect('simulador')

        messages.error(
            request,
            "Usuario o contraseña incorrectos."
        )

    return render(
        request,
        'users/login.html',
        {
            'GOOGLE_CLIENT_ID': settings.GOOGLE_CLIENT_ID
        }
    )


@require_POST
def login_google_view(request):
    """
    Valida el ID token enviado por Google Identity Services.
    """

    credential = request.POST.get('credential')

    if not credential:
        return JsonResponse(
            {
                'error': 'No se recibió la credencial de Google.'
            },
            status=400
        )

    try:

        # Validar el token contra el Client ID de nuestra aplicación.
        idinfo = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

        # Validar el emisor del token.
        if idinfo.get('iss') not in [
            'accounts.google.com',
            'https://accounts.google.com'
        ]:
            raise ValueError('Emisor de token no válido.')

        # Verificar que Google confirmó el correo.
        if not idinfo.get('email_verified'):
            raise ValueError(
                'El correo de Google no está verificado.'
            )

        google_id = idinfo.get('sub')
        email = idinfo.get('email', '').strip().lower()

        first_name = idinfo.get(
            'given_name',
            ''
        ).strip()

        family_name = idinfo.get(
            'family_name',
            ''
        ).strip()

        if not google_id or not email:
            raise ValueError(
                'Google no proporcionó los datos necesarios.'
            )

    except ValueError:

        return JsonResponse(
            {
                'error': (
                    'La credencial de Google no es válida '
                    'o ha expirado.'
                )
            },
            status=401
        )

    # ==========================================================
    # 1. BUSCAR POR GOOGLE ID
    # ==========================================================

    usuario = CustomUser.objects.filter(
        google_id=google_id
    ).first()

    if usuario:

        login(request, usuario)

        return JsonResponse(
            {
                'redirect_url': reverse(
                    'cliente_dashboard'
                )
            }
        )

    # ==========================================================
    # 2. BUSCAR CUENTA EXISTENTE POR CORREO
    # ==========================================================

    usuario = CustomUser.objects.filter(
        email__iexact=email,
        role='cliente'
    ).first()

    if usuario:

        # Vincular la cuenta existente con Google.
        usuario.google_id = google_id

        if not usuario.first_name:
            usuario.first_name = first_name

        if not usuario.primer_apellido:
            usuario.primer_apellido = family_name

        usuario.save(
            update_fields=[
                'google_id',
                'first_name',
                'primer_apellido'
            ]
        )

        login(request, usuario)

        return JsonResponse(
            {
                'redirect_url': reverse(
                    'cliente_dashboard'
                )
            }
        )

    # ==========================================================
    # 3. USUARIO NUEVO
    # ==========================================================

    request.session['google_registro'] = {
        'google_id': google_id,
        'email': email,
        'first_name': first_name,
        'family_name': family_name,
    }

    return JsonResponse(
        {
            'redirect_url': reverse(
                'completar_registro_google'
            )
        }
    )


def completar_registro_google_view(request):
    """
    Completa el registro de un usuario nuevo que llegó desde Google.

    Google ya proporcionó nombre, apellido, correo e ID.
    Solicitamos únicamente los datos obligatorios de JERD-Cash.
    """

    datos_google = request.session.get(
        'google_registro'
    )

    if not datos_google:

        messages.error(
            request,
            "La sesión de registro con Google ha expirado."
        )

        return redirect('login')

    if request.method == 'POST':

        cedula = request.POST.get(
            'cedula',
            ''
        ).strip()

        acepta_terminos = (
            'acepta_terminos'
            in request.POST
        )

        if not cedula:

            messages.error(
                request,
                "La cédula / NIT es obligatoria."
            )

            return render(
                request,
                'users/completar_registro_google.html',
                {
                    'datos_google': datos_google
                }
            )

        if not acepta_terminos:

            messages.error(
                request,
                "Debes aceptar los Términos y Condiciones "
                "y la Política de Datos."
            )

            return render(
                request,
                'users/completar_registro_google.html',
                {
                    'datos_google': datos_google
                }
            )

        # Verificar que la cédula no esté registrada.
        if CustomUser.objects.filter(
            cedula=cedula
        ).exists():

            messages.error(
                request,
                "La cédula / NIT ya está registrada."
            )

            return render(
                request,
                'users/completar_registro_google.html',
                {
                    'datos_google': datos_google
                }
            )

        # Crear un username interno único.
        username = (
            'google_'
            + secrets.token_hex(8)
        )

        x_forwarded_for = request.META.get(
            'HTTP_X_FORWARDED_FOR'
        )

        ip_address = (
            x_forwarded_for.split(',')[0].strip()
            if x_forwarded_for
            else request.META.get('REMOTE_ADDR')
        )

        try:

            usuario = CustomUser(
                first_name=datos_google.get(
                    'first_name',
                    ''
                ),
                last_name=datos_google.get(
                    'family_name',
                    ''
                ),
                primer_apellido=datos_google.get(
                    'family_name',
                    ''
                ),
                username=username,
                email=datos_google.get(
                    'email'
                ),
                cedula=cedula,
                google_id=datos_google.get(
                    'google_id'
                ),
                role='cliente'
            )

            # Cuenta autenticada mediante Google.
            # No necesita una contraseña local.
            usuario.set_unusable_password()

            usuario.save()

            # Crear automáticamente el perfil del cliente.
            PerfilCliente.objects.get_or_create(
                usuario=usuario
            )

            # Registrar aceptación legal.
            ConsentimientoLegal.objects.create(
                usuario=usuario,
                ip_address=ip_address,
                version_documento="1.0",
                tipo_documento="TyC_Politica_Datos"
            )

        except IntegrityError:

            messages.error(
                request,
                "No fue posible crear la cuenta. "
                "Algunos datos ya están registrados."
            )

            return render(
                request,
                'users/completar_registro_google.html',
                {
                    'datos_google': datos_google
                }
            )

        # Limpiar información temporal.
        request.session.pop(
            'google_registro',
            None
        )

        # Iniciar sesión automáticamente.
        login(
            request,
            usuario
        )

        messages.success(
            request,
            "Cuenta creada correctamente. "
            "Bienvenido a JERD-Cash."
        )

        return redirect(
            'cliente_dashboard'
        )

    return render(
        request,
        'users/completar_registro_google.html',
        {
            'datos_google': datos_google
        }
    )


class TerminosCondicionesView(TemplateView):
    """
    Vista pública para mostrar los Términos y Condiciones.
    """

    template_name = 'users/terminos.html'