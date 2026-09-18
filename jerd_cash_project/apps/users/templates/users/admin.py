from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, ConsentimientoLegal


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):

    list_display = (
        'username',
        'first_name',
        'primer_apellido',
        'email',
        'cedula',
        'role',
        'is_active',
    )

    list_filter = (
        'role',
        'is_active',
        'is_staff',
    )

    search_fields = (
        'username',
        'first_name',
        'primer_apellido',
        'segundo_apellido',
        'email',
        'cedula',
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            'Información personal JERD-Cash',
            {
                'fields': (
                    'cedula',
                    'segundo_nombre',
                    'primer_apellido',
                    'segundo_apellido',
                    'role',
                )
            }
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'Información personal JERD-Cash',
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'cedula',
                    'segundo_nombre',
                    'primer_apellido',
                    'segundo_apellido',
                    'role',
                )
            }
        ),
    )


@admin.register(ConsentimientoLegal)
class ConsentimientoLegalAdmin(admin.ModelAdmin):

    list_display = (
        'usuario',
        'fecha_hora',
        'ip_address',
        'version_documento',
        'tipo_documento',
    )

    list_filter = (
        'version_documento',
        'tipo_documento',
    )

    search_fields = (
        'usuario__username',
        'usuario__email',
        'usuario__cedula',
    )