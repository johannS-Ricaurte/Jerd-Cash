# apps/users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('registro/', views.registro_view, name='registro'),
    path('terminos-y-condiciones/', views.TerminosCondicionesView.as_view(), name='terminos'),
    path('login/', views.login_view, name='login'), # Se hará en la Fase 2
]