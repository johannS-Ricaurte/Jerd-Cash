
import re

from django.db import transaction
from django.core.exceptions import ValidationError

from .models import CustomUser, ConsentimientoLegal


def registrar_usuario_con_consentimiento(
    first_name,
    primer_apellido,
    username,
    email,
    password,
    cedula,
    ip_address,
    acepta_terminos
):
    """
    Servicio para registrar un usuario y su consentimiento legal
    de forma atómica.
    """

    # Validar aceptación de términos y condiciones.
    if not acepta_terminos:
        raise ValidationError(
            "Es obligatorio aceptar los Términos y Condiciones "
            "y la Política de Datos para registrarse."
        )

    # Evitar errores si la contraseña llega vacía o como None.
    password = password or ''

    # Validar que contenga al menos una letra mayúscula.
    tiene_mayuscula = re.search(
        r'[A-Z]',
        password
    )

    # Validar que contenga un punto.
    tiene_punto = '.' in password

    # Caracteres especiales permitidos para esta validación.
    caracteres_especiales = "!@#$%^&*_-+=/?¿¡:;,(){}[]<>|\\'\""

    # Validar que contenga al menos un carácter especial.
    tiene_especial = any(
        caracter in caracteres_especiales
        for caracter in password
    )

    # Rechazar la contraseña si falta algún requisito.
    if not tiene_mayuscula or not tiene_punto or not tiene_especial:
        raise ValidationError(
            "La contraseña debe contener al menos una letra "
            "mayúscula, un punto (.) y un carácter especial, "
            "por ejemplo !, @, # o $."
        )

    # Crear usuario y consentimiento en una transacción atómica.
    with transaction.atomic():

        usuario = CustomUser.objects.create_user(
            first_name=first_name,
            username=username,
            email=email,
            password=password,
            cedula=cedula,
            primer_apellido=primer_apellido,
            role='cliente'
        )

        ConsentimientoLegal.objects.create(
            usuario=usuario,
            ip_address=ip_address,
            version_documento="1.0",
            tipo_documento="TyC_Politica_Datos"
        )

    return usuario
