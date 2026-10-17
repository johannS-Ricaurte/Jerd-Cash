from django.contrib import admin
from .models import ConfiguracionPago


@admin.register(ConfiguracionPago)
class ConfiguracionPagoAdmin(admin.ModelAdmin):

    list_display = (
        'entidad',
        'llave',
        'titular',
        'fecha_actualizacion',
    )

    search_fields = (
        'entidad',
        'llave',
        'titular',
    )

    readonly_fields = (
        'fecha_actualizacion',
    )