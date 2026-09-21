from django.db import models
from django.conf import settings


class PerfilCliente(models.Model):

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_cliente'
    )

    nacionalidad = models.CharField(
        max_length=100,
        blank=True
    )

    ciudad_nacimiento = models.CharField(
        max_length=100,
        blank=True
    )

    pais_residencia = models.CharField(
        max_length=100,
        blank=True
    )

    ciudad_residencia = models.CharField(
        max_length=100,
        blank=True
    )

    telefono = models.CharField(
        max_length=20,
        blank=True
    )

    direccion = models.CharField(
        max_length=200,
        blank=True
    )

    contacto_respaldo_nombre = models.CharField(
        max_length=150,
        blank=True
    )

    contacto_respaldo_telefono = models.CharField(
        max_length=20,
        blank=True
    )

    contacto_respaldo_parentesco = models.CharField(
        max_length=50,
        blank=True
    )

    ingresos_mensuales = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    gastos_mensuales = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


class SolicitudCredito(models.Model):

    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='solicitudes_credito'
    )

    monto_solicitado = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    plazo_meses = models.IntegerField(
    default=12
)

    cedula = models.FileField(
        upload_to='solicitudes/cedulas/'
    )

    recibo = models.FileField(
        upload_to='solicitudes/recibos/'
    )

    certificacion_bancaria = models.FileField(
        upload_to='solicitudes/certificaciones_bancarias/'
    )

    extracto_bancario_1 = models.FileField(
        upload_to='solicitudes/extractos/',
        blank=True,
        null=True
    )

    extracto_bancario_2 = models.FileField(
        upload_to='solicitudes/extractos/',
        blank=True,
        null=True
    )

    extracto_bancario_3 = models.FileField(
        upload_to='solicitudes/extractos/',
        blank=True,
        null=True
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='PENDIENTE'
    )

    fecha_solicitud = models.DateTimeField(
        auto_now_add=True
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"Solicitud #{self.id} - "
            f"{self.usuario.username} - "
            f"{self.estado}"
        )