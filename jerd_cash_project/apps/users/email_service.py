import logging

from django.conf import settings
from django.core.mail import send_mail


logger = logging.getLogger(__name__)


def enviar_notificacion(destinatario, asunto, mensaje):
    """
    Envía una notificación por correo electrónico.
    Si el envío falla, registra el error sin interrumpir
    la operación principal de JERD-Cash.
    """

    if not destinatario:
        logger.warning(
            "No se envió el correo porque el destinatario está vacío."
        )
        return False

    try:
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            fail_silently=False,
        )
        return True

    except Exception:
        logger.exception(
            "Error enviando una notificación a %s",
            destinatario,
        )
        return False