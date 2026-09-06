# apps/users/services.py

from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from .models import CustomUser, ConsentimientoLegal

def registrar_usuario_con_consentimiento(username, email, password, cedula, ip_address, acepta_terminos):
    """
    Servicio para registrar un usuario y su consentimiento legal de forma atómica.
    
    Args:
        username (str): Nombre de usuario.
        email (str): Correo electrónico.
        password (str): Contraseña en texto plano (se hasheará internamente).
        cedula (str): Número de identificación.
        ip_address (str): IP desde donde se realiza el registro.
        acepta_terminos (bool): Flag que indica si el usuario marcó el checkbox.
        
    Returns:
        CustomUser: El usuario creado exitosamente.
        
    Raises:
        ValidationError: Si no se aceptan los términos o hay datos inválidos.
    """
    # 1. Validación de negocio obligatoria
    if not acepta_terminos:
        raise ValidationError("Es obligatorio aceptar los Términos y Condiciones y la Política de Datos para registrarse.")

    # 2. Transacción atómica: Si falla algo, no se guarda nada (integridad de datos)
    with transaction.atomic():
        # Crear el usuario (Django se encarga de hashear la contraseña con Argon2/PBKDF2)
        usuario = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            cedula=cedula,
            role='cliente' # Por defecto, el registro público es para clientes
        )
        
        # Crear el registro de auditoría del consentimiento (Ley 1581)
        ConsentimientoLegal.objects.create(
            usuario=usuario,
            ip_address=ip_address,
            version_documento="1.0",
            tipo_documento="TyC_Politica_Datos"
        )
        
    return usuario