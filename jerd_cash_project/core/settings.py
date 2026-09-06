# core/settings.py

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ... (SECRET_KEY, DEBUG, ALLOWED_HOSTS se mantienen normales) ...

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps propias (formato completo con AppConfig)
    'apps.users.apps.UsersConfig',
    'apps.loans.apps.LoansConfig',
]

# Configuración de Seguridad Robusta (Requisito Ley 1273 de 2009)
# 1. Forzar HTTPS en producción (descomentar en producción)
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000  # 1 año
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# 2. Protección de Cookies de Sesión (Mitiga robo de sesión)
SESSION_COOKIE_SECURE = True          # Solo se transmite por HTTPS
SESSION_COOKIE_HTTPONLY = True        # Inaccesible para JavaScript (mitiga XSS)
SESSION_COOKIE_SAMESITE = 'Strict'    # Mitiga ataques CSRF

# 3. Protección de Cookie CSRF
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# 4. Cabeceras de seguridad adicionales
SECURE_BROWSER_XSS_FILTER = True      # Activa el filtro XSS del navegador
SECURE_CONTENT_TYPE_NOSNIFF = True    # Previene MIME-type sniffing
X_FRAME_OPTIONS = 'DENY'              # Previene ataques de Clickjacking

# Configuración del Modelo de Usuario Personalizado
AUTH_USER_MODEL = 'users.CustomUser'

# ... (RESTO DE CONFIGURACIÓN DE BASE DE DATOS, STATIC, ETC.) ...