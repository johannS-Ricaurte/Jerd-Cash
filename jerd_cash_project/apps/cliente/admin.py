from django.contrib import admin

from .models import PerfilCliente, SolicitudCredito


@admin.register(PerfilCliente)
class PerfilClienteAdmin(admin.ModelAdmin):
    list_display = (
        'usuario',
        'telefono',
        'ciudad_residencia',
        'fecha_actualizacion',
    )


@admin.register(SolicitudCredito)
class SolicitudCreditoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'usuario',
        'monto_solicitado',
        'estado',
        'fecha_solicitud',
    )

    list_filter = (
        'estado',
    )

    search_fields = (
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
        'usuario__email',
    )