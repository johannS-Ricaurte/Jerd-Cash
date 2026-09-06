# apps/users/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView
from .services import registrar_usuario_con_consentimiento
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login

def home_view(request):
    return render(request, 'users/home.html')

def registro_view(request):
    """
    Vista para manejar el registro de nuevos clientes.
    """
    if request.method == 'POST':
        # Extracción de datos del formulario
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        cedula = request.POST.get('cedula')
        # 'acepta_terminos' solo existe en POST si el checkbox fue marcado
        acepta_terminos = 'acepta_terminos' in request.POST 
        
        # Obtener la IP del cliente (considerando proxies como Nginx/Heroku)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

        try:
            # Llamada a la capa de lógica (Servicio)
            registrar_usuario_con_consentimiento(
                username=username,
                email=email,
                password=password,
                cedula=cedula,
                ip_address=ip_address,
                acepta_terminos=acepta_terminos
            )
            messages.success(request, "Registro exitoso. Bienvenido a JERD-Cash.")
            return redirect('login') # Redirigir al login tras éxito
            
        except ValidationError as e:
            # Si el servicio rechaza la petición (ej. no aceptó TyC)
            messages.error(request, str(e))
        except Exception as e:
            # Manejo genérico de errores (ej. cedula duplicada)
            messages.error(request, "Ocurrió un error durante el registro. Verifique los datos.")

    return render(request, 'users/register.html')

def login_view(request):
    """
    Vista para iniciar sesión.
    Compatible con CustomUser (usa authenticate con username).
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        usuario = authenticate(request, username=username, password=password)

        if usuario is not None:
            login(request, usuario)
            messages.success(request, f"Bienvenido, {usuario.username}.")
            # Por ahora redirige a registro; después lo cambiaremos al dashboard
            return redirect('registro')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, 'users/login.html')

def login_view(request):
    """Vista para iniciar sesión compatible con CustomUser."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        usuario = authenticate(request, username=username, password=password)
        
        if usuario is not None:
            login(request, usuario)
            messages.success(request, f"Bienvenido, {usuario.username}.")
            # Por ahora redirige a registro para probar; luego lo cambiaremos al Dashboard
            return redirect('simulador') 
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
            
    return render(request, 'users/login.html')


class TerminosCondicionesView(TemplateView):
    """
    Vista pública para mostrar los Términos y Condiciones.
    Accesible sin necesidad de estar autenticado.
    """
    template_name = 'users/terminos.html'