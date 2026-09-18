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

    if not acepta_terminos:
        raise ValidationError(
            "Es obligatorio aceptar los Términos y Condiciones "
            "y la Política de Datos para registrarse."
        )

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