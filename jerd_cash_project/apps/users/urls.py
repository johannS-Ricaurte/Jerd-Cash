from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [

    path(
        'registro/',
        views.registro_view,
        name='registro'
    ),

    path(
        'terminos-y-condiciones/',
        views.TerminosCondicionesView.as_view(),
        name='terminos'
    ),

    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'login/google/',
        views.login_google_view,
        name='login_google'
    ),

    path(
        'registro/google/',
        views.completar_registro_google_view,
        name='completar_registro_google'
    ),

    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page='home'),
        name='logout'
    ),

]