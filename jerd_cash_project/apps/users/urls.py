from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .password_forms import JERDPasswordResetForm

from . import views


urlpatterns = [

    # Registro de usuarios
    path(
        'registro/',
        views.registro_view,
        name='registro'
    ),

    # Términos y condiciones
    path(
        'terminos-y-condiciones/',
        views.TerminosCondicionesView.as_view(),
        name='terminos'
    ),

    # Política de Tratamiento de Datos Personales
    path(
        'politica-de-datos/',
        views.PoliticaDatosView.as_view(),
        name='politica_datos'
    ),

    # Inicio de sesión
    path(
        'login/',
        views.login_view,
        name='login'
    ),

    # Inicio de sesión con Google
    path(
        'login/google/',
        views.login_google_view,
        name='login_google'
    ),

    # Completar registro con Google
    path(
        'registro/google/',
        views.completar_registro_google_view,
        name='completar_registro_google'
    ),

    # Cerrar sesión
    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page='home'),
        name='logout'
    ),

    # ==========================================
    # RECUPERACIÓN DE CONTRASEÑA
    # ==========================================

    # 1. Formulario para solicitar el correo
    path(
        'recuperar-contrasena/',
        auth_views.PasswordResetView.as_view(
            template_name='users/password_reset_form.html',
            email_template_name='users/password_reset_email.html',
            subject_template_name='users/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done')
        ),
        name='password_reset'
    ),

    # 2. Confirmación de solicitud
    path(
        'recuperar-contrasena/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    # 3. Formulario para establecer la nueva contraseña
    path(
        'restablecer-contrasena/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
            form_class=JERDPasswordResetForm,
            success_url=reverse_lazy('password_reset_complete')
        ),
        name='password_reset_confirm'
    ),


    # 4. Confirmación de contraseña restablecida
    path(
        'restablecer-contrasena/completado/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),


]