from django.urls import path
from . import views

urlpatterns = [
    path(
        'simulador/',
        views.simulador_view,
        name='simulador'
    ),

    path(
        'calcular-simulacion/',
        views.calcular_simulacion_ajax,
        name='calcular_simulacion'
    ),

    path(
        'simulador-publico/',
        views.simulador_publico_view,
        name='simulador_publico'
    ),
]

