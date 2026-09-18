# apps/users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado. Extiende al usuario base de Django.
    """
    ROLE_CHOICES = (
        ('cliente', 'Cliente'),
        ('empleado', 'Empleado'),
        ('administrador', 'Administrador'),
    )
    
    # Campos adicionales requeridos por el dominio financiero
    cedula = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Cédula / NIT")

    google_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    segundo_nombre = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Segundo nombre"
    )

    primer_apellido = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Primer apellido"
    )

    segundo_apellido = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Segundo apellido"
    )
    
    role = models.CharField(
        max_length=15, 
        choices=ROLE_CHOICES, 
        default='cliente')
    
    # NOTA PARA SUSTENTACIÓN: En la Fase 2, el campo 'cedula' se envolverá 
    # con un decorador de cifrado (ej. django-cryptography) para cumplir 
    # con el cifrado en reposo de la Ley 1273.

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class ConsentimientoLegal(models.Model):
    """
    Modelo de Auditoría para Términos y Condiciones.
    Cumple con la Ley 1581 de 2012 y Decreto 1377 de 2013 al guardar 
    evidencia técnica verificable de la aceptación del usuario.
    """
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='consentimientos')
    fecha_hora = models.DateTimeField(default=timezone.now, verbose_name="Fecha y hora de aceptación")
    ip_address = models.GenericIPAddressField(verbose_name="Dirección IP del registro")
    version_documento = models.CharField(max_length=10, default="1.0", verbose_name="Versión del documento")
    tipo_documento = models.CharField(max_length=50, default="TyC_Politica_Datos", verbose_name="Tipo de documento aceptado")

    class Meta:
        verbose_name = "Registro de Consentimiento"
        verbose_name_plural = "Registros de Consentimiento"
        # Garantiza que no se pueda duplicar el mismo registro exacto para el mismo usuario y versión
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'version_documento', 'tipo_documento'], name='unico_consentimiento_por_version')
        ]

    def __str__(self):
        return f"Consentimiento de {self.usuario.username} - {self.fecha_hora.strftime('%Y-%m-%d %H:%M')}"