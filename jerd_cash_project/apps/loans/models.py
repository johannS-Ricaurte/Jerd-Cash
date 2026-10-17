from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Prestamo(models.Model):
    ESTADO_CHOICES = (
        ('solicitado', 'Solicitado'),
        ('evaluado', 'Evaluado'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('desembolsado', 'Desembolsado'),
        ('pagado', 'Pagado'),
        ('mora', 'En Mora'),
    )

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prestamos',
        verbose_name="Cliente solicitante"
    )

    monto_solicitado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('100000'))],
        verbose_name="Monto solicitado (COP)"
    )

    plazo_meses = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(36)],
        verbose_name="Plazo en meses"
    )

    tasa_interes_mensual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Tasa de interés mensual (%)"
    )

    score_calculado = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Score determinístico"
    )

    nivel_riesgo = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Nivel de riesgo"
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='solicitado'
    )

    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Préstamo"
        verbose_name_plural = "Préstamos"
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Préstamo #{self.id} - {self.cliente.username} - ${self.monto_solicitado}"


class Cuota(models.Model):
    prestamo = models.ForeignKey(
        Prestamo,
        on_delete=models.CASCADE,
        related_name='cuotas',
        verbose_name="Préstamo"
    )

    numero_cuota = models.IntegerField(verbose_name="Número de cuota")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de vencimiento")

    valor_cuota = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Valor cuota"
    )
    interes = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Interés período"
    )
    abono_capital = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Abono capital"
    )
    saldo_pendiente = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Saldo pendiente"
    )

    pagada = models.BooleanField(default=False, verbose_name="¿Pagada?")

    dias_mora = models.IntegerField(default=0)
    monto_mora = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    

    class Meta:
        verbose_name = "Cuota"
        verbose_name_plural = "Cuotas"
        ordering = ['numero_cuota']
        unique_together = ['prestamo', 'numero_cuota']

    def __str__(self):
        return f"Cuota {self.numero_cuota} - Préstamo #{self.prestamo.id}"


class Pago(models.Model):

    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('pendiente_confirmacion', 'Pendiente de confirmación'),
        ('exitoso', 'Pago exitoso'),
        ('rechazado', 'Rechazado'),
    ]

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pagos',
        verbose_name='Cliente'
    )

    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Monto del pago'
    )

    comprobante = models.FileField(
        upload_to='pagos/comprobantes/',
        null=True,
        blank=True,
        verbose_name='Comprobante de pago'
    )

    estado = models.CharField(
        max_length=30,
        choices=ESTADOS,
        default='pendiente',
        verbose_name='Estado'
    )

    fecha_pago = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha del pago'
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    motivo_rechazo = models.TextField(
        blank=True,
        null=True,
        verbose_name='Motivo del rechazo'
    )

    def __str__(self):
        return (
            f'Pago #{self.id} - '
            f'{self.cliente.username} - '
            f'${self.monto}'
        )
    

class PagoCuota(models.Model):
    pago = models.ForeignKey(
        Pago,
        on_delete=models.CASCADE,
        related_name='cuotas_pagadas'
    )

    cuota = models.ForeignKey(
        Cuota,
        on_delete=models.CASCADE,
        related_name='pagos'
    )

    monto_aplicado = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    # Datos históricos de la mora al momento del pago
    dias_mora = models.IntegerField(default=0)

    monto_mora = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    fecha_aplicacion = models.DateTimeField(auto_now_add=True)

    
    def __str__(self):
        return (
            f'Pago #{self.pago.id} → '
            f'Cuota #{self.cuota.numero_cuota}'
        )
    
