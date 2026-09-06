# core/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.users.urls')), # Incluye las URLs de usuarios
    path('prestamos/', include('apps.loans.urls')), # Fase 2
]