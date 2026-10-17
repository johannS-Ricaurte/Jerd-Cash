from django.db import models


class ConfiguracionPago(models.Model):

    qr = models.ImageField(
        upload_to='configuracion/pagos/',
        verbose_name='Código QR'
    )

    entidad = models.CharField(
        max_length=100,
        verbose_name='Entidad o billetera'
    )

    llave = models.CharField(
        max_length=150,
        verbose_name='Llave de transferencia'
    )

    titular = models.CharField(
        max_length=150,
        verbose_name='Titular de la cuenta'
    )

    instrucciones = models.TextField(
        blank=True,
        verbose_name='Instrucciones para el cliente'
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    def __str__(self):
        return f'Configuración de pago - {self.entidad}'