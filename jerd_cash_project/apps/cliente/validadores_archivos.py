
from pathlib import Path

import pymupdf
from PIL import Image, UnidentifiedImageError
from django.core.exceptions import ValidationError


TAMANO_MAXIMO = 5 * 1024 * 1024  # 5 MB


def validar_documento(archivo, tipo):
    """
    Valida tamaño, extensión y contenido real
    de documentos PDF e imágenes JPG/PNG.
    """

    if not archivo:
        return archivo

    if archivo.size > TAMANO_MAXIMO:
        raise ValidationError(
            "El archivo no puede superar los 5 MB."
        )

    extension = Path(archivo.name).suffix.lower()

    try:
        archivo.seek(0)

        if tipo == "pdf":
            if extension != ".pdf":
                raise ValidationError(
                    "El documento debe estar en formato PDF."
                )

            with pymupdf.open(
                stream=archivo.read(),
                filetype="pdf"
            ) as documento:
                if documento.page_count < 1:
                    raise ValidationError(
                        "El PDF debe contener al menos una página."
                    )

        elif tipo == "imagen":
            if extension not in (".jpg", ".jpeg", ".png"):
                raise ValidationError(
                    "La imagen debe estar en formato JPG o PNG."
                )

            with Image.open(archivo) as imagen:
                formato = imagen.format
                imagen.verify()

            if formato not in ("JPEG", "PNG"):
                raise ValidationError(
                    "El contenido no corresponde a una imagen JPG o PNG válida."
                )

        else:
            raise ValidationError(
                "Tipo de archivo no permitido."
            )

    except ValidationError:
        raise

    except (
        pymupdf.FileDataError,
        pymupdf.EmptyFileError,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ):
        raise ValidationError(
            "El archivo está dañado o no tiene un formato válido."
        )

    finally:
        archivo.seek(0)

    return archivo
