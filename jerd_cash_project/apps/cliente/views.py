from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse

from .forms import (
    PerfilClienteForm,
    SolicitudCreditoForm,
    CIUDADES_POR_PAIS
)

from .models import (
    PerfilCliente,
    SolicitudCredito
)

from .ocr import (
    analizar_cedula,
    analizar_extracto_bancario
)


@login_required
def dashboard_view(request):
    return render(
        request,
        'cliente/dashboard.html'
    )


@login_required
def perfil_view(request):

    perfil, creado = PerfilCliente.objects.get_or_create(
        usuario=request.user
    )

    if request.method == 'POST':

        form = PerfilClienteForm(
            request.POST,
            instance=perfil,
            usuario=request.user
        )

        if form.is_valid():

            form.save()

            return redirect('perfil')

    else:

        form = PerfilClienteForm(
            instance=perfil,
            usuario=request.user
        )

    return render(
        request,
        'cliente/perfil.html',
        {
            'form': form,
            'ciudades_por_pais': CIUDADES_POR_PAIS,
        }
    )


@login_required
def solicitar_credito_view(request):

    if request.method == 'POST':

        form = SolicitudCreditoForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            # ==========================================
            # VALIDAR CEDULA
            # ==========================================

            archivo_cedula = request.FILES.get(
                'cedula'
            )

            if not archivo_cedula:

                form.add_error(
                    'cedula',
                    'Debe adjuntar su cedula en formato PDF.'
                )

            else:

                try:

                    resultado_cedula = analizar_cedula(
                        archivo_cedula
                    )

                    if not resultado_cedula['es_cedula']:

                        form.add_error(
                            'cedula',
                            (
                                'El archivo que esta intentando subir '
                                'no corresponde a una cedula. Debe subir '
                                'una cedula para continuar con el proceso.'
                            )
                        )

                except Exception:

                    form.add_error(
                        'cedula',
                        (
                            'No fue posible analizar el documento. '
                            'Verifique que el PDF sea valido.'
                        )
                    )

            # ==========================================
            # VALIDAR EXTRACTO 1
            # ==========================================

            archivo_extracto_1 = request.FILES.get(
                'extracto_bancario_1'
            )

            contrasena_extracto_1 = request.POST.get(
                'contrasena_extracto_1',
                ''
            )

            if not archivo_extracto_1:

                form.add_error(
                    'extracto_bancario_1',
                    'Debe adjuntar el primer extracto bancario.'
                )

            else:

                try:

                    resultado_extracto_1 = analizar_extracto_bancario(
                        archivo_extracto_1,
                        contrasena_extracto_1
                    )

                    if not resultado_extracto_1['es_extracto']:

                        form.add_error(
                            'extracto_bancario_1',
                            (
                                'El primer archivo no parece '
                                'corresponder a un extracto bancario.'
                            )
                        )

                except ValueError as error:

                    form.add_error(
                        'extracto_bancario_1',
                        str(error)
                    )

                except Exception:

                    form.add_error(
                        'extracto_bancario_1',
                        (
                            'No fue posible analizar el primer '
                            'extracto bancario.'
                        )
                    )

            # ==========================================
            # VALIDAR EXTRACTO 2
            # ==========================================

            archivo_extracto_2 = request.FILES.get(
                'extracto_bancario_2'
            )

            contrasena_extracto_2 = request.POST.get(
                'contrasena_extracto_2',
                ''
            )

            if not archivo_extracto_2:

                form.add_error(
                    'extracto_bancario_2',
                    'Debe adjuntar el segundo extracto bancario.'
                )

            else:

                try:

                    resultado_extracto_2 = analizar_extracto_bancario(
                        archivo_extracto_2,
                        contrasena_extracto_2
                    )

                    if not resultado_extracto_2['es_extracto']:

                        form.add_error(
                            'extracto_bancario_2',
                            (
                                'El segundo archivo no parece '
                                'corresponder a un extracto bancario.'
                            )
                        )

                except ValueError as error:

                    form.add_error(
                        'extracto_bancario_2',
                        str(error)
                    )

                except Exception:

                    form.add_error(
                        'extracto_bancario_2',
                        (
                            'No fue posible analizar el segundo '
                            'extracto bancario.'
                        )
                    )

            # ==========================================
            # VALIDAR EXTRACTO 3
            # ==========================================

            archivo_extracto_3 = request.FILES.get(
                'extracto_bancario_3'
            )

            contrasena_extracto_3 = request.POST.get(
                'contrasena_extracto_3',
                ''
            )

            if not archivo_extracto_3:

                form.add_error(
                    'extracto_bancario_3',
                    'Debe adjuntar el tercer extracto bancario.'
                )

            else:

                try:

                    resultado_extracto_3 = analizar_extracto_bancario(
                        archivo_extracto_3,
                        contrasena_extracto_3
                    )

                    if not resultado_extracto_3['es_extracto']:

                        form.add_error(
                            'extracto_bancario_3',
                            (
                                'El tercer archivo no parece '
                                'corresponder a un extracto bancario.'
                            )
                        )

                except ValueError as error:

                    form.add_error(
                        'extracto_bancario_3',
                        str(error)
                    )

                except Exception:

                    form.add_error(
                        'extracto_bancario_3',
                        (
                            'No fue posible analizar el tercer '
                            'extracto bancario.'
                        )
                    )

            # ==========================================
            # GUARDAR SOLICITUD
            # ==========================================

            if form.is_valid():

                solicitud = form.save(
                    commit=False
                )

                solicitud.usuario = request.user

                solicitud.save()

                return redirect(
                    'cliente_dashboard'
                )

    else:

        form = SolicitudCreditoForm()

    return render(
        request,
        'cliente/solicitar_credito.html',
        {
            'form': form
        }
    )


@login_required
def validar_cedula_ajax(request):

    if request.method != 'POST':

        return JsonResponse(
            {
                'valida': False,
                'mensaje': 'Metodo no permitido.'
            },
            status=405
        )

    archivo = request.FILES.get(
        'cedula'
    )

    if not archivo:

        return JsonResponse(
            {
                'valida': False,
                'mensaje': 'Debe seleccionar un archivo.'
            },
            status=400
        )

    if not archivo.name.lower().endswith('.pdf'):

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'La cedula debe estar en formato PDF.'
                )
            }
        )

    try:

        resultado = analizar_cedula(
            archivo
        )

        if resultado['es_cedula']:

            return JsonResponse(
                {
                    'valida': True,
                    'mensaje': (
                        'El documento parece corresponder '
                        'a una cedula.'
                    )
                }
            )

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'El archivo que esta intentando subir '
                    'no corresponde a una cedula. Debe subir '
                    'una cedula para continuar con el proceso.'
                )
            }
        )

    except Exception:

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'No fue posible analizar el documento. '
                    'Verifique que el PDF sea valido.'
                )
            },
            status=500
        )


@login_required
def validar_extracto_ajax(request):

    if request.method != 'POST':

        return JsonResponse(
            {
                'valida': False,
                'mensaje': 'Metodo no permitido.'
            },
            status=405
        )

    archivo = request.FILES.get(
        'extracto'
    )

    contrasena = request.POST.get(
        'contrasena',
        ''
    )

    if not archivo:

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'Debe seleccionar un extracto bancario.'
                )
            },
            status=400
        )

    if not archivo.name.lower().endswith('.pdf'):

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'El extracto bancario debe estar '
                    'en formato PDF.'
                )
            }
        )

    try:

        resultado = analizar_extracto_bancario(
            archivo,
            contrasena
        )

        if resultado['es_extracto']:

            return JsonResponse(
                {
                    'valida': True,
                    'mensaje': (
                        'El extracto bancario fue validado '
                        'correctamente.'
                    )
                }
            )

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'El documento no parece corresponder '
                    'a un extracto bancario.'
                )
            }
        )

    except ValueError as error:

        return JsonResponse(
            {
                'valida': False,
                'mensaje': str(error)
            }
        )

    except Exception:

        return JsonResponse(
            {
                'valida': False,
                'mensaje': (
                    'No fue posible analizar el extracto. '
                    'Verifique el archivo y la contraseña.'
                )
            },
            status=500
        )


@login_required
def mis_solicitudes_view(request):

    solicitudes = SolicitudCredito.objects.filter(
        usuario=request.user
    ).order_by(
        '-fecha_solicitud'
    )

    return render(
        request,
        'cliente/mis_solicitudes.html',
        {
            'solicitudes': solicitudes
        }
    )

