import io
import re
import unicodedata
import pymupdf
import pytesseract
from PIL import Image, ImageOps, ImageEnhance



pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def normalizar_texto(texto):
    texto = texto.upper()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    return texto


def extraer_texto_pdf(archivo, contrasena=None):
    """
    Extrae texto directamente del PDF cuando es posible.
    Si el PDF no contiene texto digital suficiente,
    utiliza OCR en español.
    """

    contenido = archivo.read()

    documento = pymupdf.open(
        stream=contenido,
        filetype="pdf"
    )

    try:
        # Desbloquear PDF protegido, si es necesario.
        if documento.needs_pass:
            if not contrasena:
                raise ValueError(
                    "El PDF está protegido y requiere contraseña."
                )

            if not documento.authenticate(contrasena):
                raise ValueError(
                    "La contraseña del PDF es incorrecta."
                )

        # 1. Intentar extraer texto digital.
        paginas_texto = []

        for pagina in documento:
            texto = pagina.get_text(
                "text",
                sort=True
            )
            paginas_texto.append(texto)

        texto_digital = "\n\n".join(paginas_texto).strip()

        # Si existe texto digital suficiente, utilizarlo.
        if len(texto_digital) >= 100:
            return texto_digital

        # 2. Si el documento es escaneado, utilizar OCR.
        paginas_ocr = []

        for pagina in documento:
            pixmap = pagina.get_pixmap(
                matrix=pymupdf.Matrix(3, 3),
                alpha=False
            )

            imagen = Image.frombytes(
                "RGB",
                [pixmap.width, pixmap.height],
                pixmap.samples
            )

            # Mejorar la imagen antes del reconocimiento.
            imagen = ImageOps.grayscale(imagen)
            imagen = ImageOps.autocontrast(imagen)

            imagen = ImageEnhance.Contrast(
                imagen
            ).enhance(1.5)

            texto_ocr = pytesseract.image_to_string(
                imagen,
                lang="spa",
                config="--psm 3"
            )

            paginas_ocr.append(texto_ocr)

        return "\n\n".join(paginas_ocr).strip()

    finally:
        documento.close()


def validar_cedula(texto):

    texto = normalizar_texto(texto)

    if texto.strip() == "":
        return False

    puntaje = 0

    if "COLOMBIA" in texto:
        puntaje = puntaje + 2

    if "CEDULA" in texto:
        puntaje = puntaje + 2

    if "CIUDADANIA" in texto:
        puntaje = puntaje + 2

    if "DECUDADANA" in texto:
        puntaje = puntaje + 2

    if "CIUDADANA" in texto:
        puntaje = puntaje + 2

    if re.search(r"\b\d{7,10}\b", texto):
        puntaje = puntaje + 2

    if re.search(r"\bP-\d+", texto):
        puntaje = puntaje + 2

    return puntaje >= 4


def validar_extracto_bancario(texto):

    texto = normalizar_texto(texto)

    if texto.strip() == "":
        return False

    puntaje = 0

    palabras_bancarias = [
        "BANCO",
        "CUENTA",
        "SALDO",
        "MOVIMIENTOS",
        "TRANSACCIONES",
        "PERIODO",
        "FECHA",
        "VALOR"
    ]

    for palabra in palabras_bancarias:

        if palabra in texto:
            puntaje = puntaje + 1

    if re.search(r"\b\d{6,20}\b", texto):
        puntaje = puntaje + 1

    return puntaje >= 4


def analizar_cedula(archivo, contrasena=None):

    texto = extraer_texto_pdf(
        archivo,
        contrasena
    )

    es_cedula = validar_cedula(texto)

    return {
        "es_cedula": es_cedula,
        "texto": texto
    }


def analizar_extracto_bancario(archivo):
    """
    Valida si una imagen corresponde aparentemente
    a un extracto bancario mediante OCR.

    No almacena ni devuelve el texto extraído.
    """

    try:
        # Volver al inicio del archivo.
        archivo.seek(0)

        # Abrir y validar que el archivo sea una imagen.
        with Image.open(archivo) as imagen:
            if imagen.format not in ("JPEG", "PNG"):
                return {"es_extracto": False}

            imagen.load()

            # Convertir a RGB para facilitar el OCR.
            imagen = imagen.convert("RGB")

            # Extraer texto temporalmente para validar.
            texto = pytesseract.image_to_string(
                imagen,
                lang="spa"
            )

        # Validar el contenido con la función existente.
        es_extracto = validar_extracto_bancario(texto)

        return {
            "es_extracto": es_extracto
        }

    except Exception:
        return {
            "es_extracto": False
        }

    finally:
        # Permitir que Django guarde el archivo completo.
        try:
            archivo.seek(0)
        except Exception:
            pass
