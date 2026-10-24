
from django.core.management.base import BaseCommand
from django.utils import timezone

from jerd_cash_project.apps.loans.models import (
    Cuota,
    Pago,
    RecordatorioCuota,
)
from jerd_cash_project.apps.users.email_service import (
    enviar_notificacion,
)


class Command(BaseCommand):
    help = (
        'Envía recordatorios de cuotas que vencen hoy '
        'o que se encuentran vencidas.'
    )

    def handle(self, *args, **options):
        hoy = timezone.localdate()

        cuotas = Cuota.objects.filter(
            pagada=False,
            prestamo__estado__in=['aprobado', 'desembolsado', 'mora'],
        ).select_related(
            'prestamo',
            'prestamo__cliente',
        )

        enviados = 0
        omitidos = 0

        for cuota in cuotas:
            # Si existe un pago pendiente de confirmación
            # asociado a esta cuota, no enviar recordatorio.
            pago_pendiente = Pago.objects.filter(
                cuotas_pagadas__cuota=cuota,
                estado='pendiente_confirmacion',
            ).exists()

            if pago_pendiente:
                omitidos += 1
                continue

            if cuota.fecha_vencimiento == hoy:
                tipo = 'vencimiento'
            elif cuota.fecha_vencimiento < hoy:
                tipo = 'mora'
            else:
                continue

            # Evitar repetir el mismo tipo de correo
            # para esta cuota durante el día actual.
            if RecordatorioCuota.objects.filter(
                cuota=cuota,
                tipo=tipo,
                fecha_envio=hoy,
            ).exists():
                continue

            cliente = cuota.prestamo.cliente

            if not cliente.email:
                self.stdout.write(
                    self.style.WARNING(
                        f'Cuota {cuota.id}: '
                        'el cliente no tiene correo.'
                    )
                )
                continue

            nombre = cliente.first_name or cliente.username
            fecha = cuota.fecha_vencimiento.strftime('%d/%m/%Y')

            if tipo == 'vencimiento':
                asunto = (
                    f'JERD-Cash: tu cuota {cuota.numero_cuota} '
                    'vence hoy'
                )

                mensaje = (
                    f'Hola {nombre},\n\n'
                    f'Te recordamos que hoy, {fecha}, '
                    f'vence la cuota {cuota.numero_cuota} '
                    f'de tu crédito Id{cuota.prestamo_id}.\n\n'
                    f'Valor de la cuota: '
                    f'${cuota.valor_cuota:,.2f} COP\n\n'
                    'Por favor, realiza el pago a tiempo '
                    'y consulta las instrucciones de pago '
                    'en JERD-Cash.\n\n'
                    'Equipo JERD-Cash'
                )

            else:
                dias_atraso = (hoy - cuota.fecha_vencimiento).days

                asunto = (
                    f'JERD-Cash: cuota {cuota.numero_cuota} '
                    'vencida'
                )

                mensaje = (
                    f'Hola {nombre},\n\n'
                    f'La cuota {cuota.numero_cuota} de tu '
                    f'crédito Id{cuota.prestamo_id} venció '
                    f'el {fecha} y continúa pendiente.\n\n'
                    f'Días transcurridos desde el vencimiento: '
                    f'{dias_atraso}\n'
                    f'Valor de la cuota: '
                    f'${cuota.valor_cuota:,.2f} COP\n\n'
                    'Te solicitamos realizar el pago lo '
                    'antes posible. Ten presente que el saldo '
                    'podría aumentar por los intereses de mora '
                    'que correspondan según las condiciones '
                    'de tu crédito.\n\n'
                    'Consulta los detalles de tu obligación '
                    'en JERD-Cash.\n\n'
                    'Equipo JERD-Cash'
                )

            resultado = enviar_notificacion(
                destinatario=cliente.email,
                asunto=asunto,
                mensaje=mensaje,
            )

            if resultado:
                RecordatorioCuota.objects.create(
                    cuota=cuota,
                    tipo=tipo,
                    fecha_envio=hoy,
                )

                enviados += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Recordatorio enviado: cuota {cuota.id}, '
                        f'tipo={tipo}.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'No se pudo enviar el recordatorio '
                        f'de la cuota {cuota.id}.'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Proceso terminado. Enviados: {enviados}. '
                f'Omitidos por pago pendiente: {omitidos}.'
            )
        )
