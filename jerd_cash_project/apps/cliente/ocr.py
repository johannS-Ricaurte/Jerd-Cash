
import re
import unicodedata
import pymupdf
import pytesseract
from PIL import Image


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

    contenido = archivo.read()

    documento = pymupdf.open(
        stream=contenido,
        filetype="pdf"
    )

    if documento.needs_pass:

        if not contrasena:
            documento.close()

            raise ValueError(
                "El PDF esta protegido con contraseña."
            )

        if not documento.authenticate(contrasena):
            documento.close()

            raise ValueError(
                "La contraseña del PDF no es correcta."
            )

    texto = ""

    for pagina in documento:

        pixmap = pagina.get_pixmap(
            matrix=pymupdf.Matrix(2, 2)
        )

        imagen = Image.frombytes(
            "RGB",
            [pixmap.width, pixmap.height],
            pixmap.samples
        )

        texto = texto + pytesseract.image_to_string(
            imagen,
            lang="spa"
        )

    documento.close()

    return texto


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


def analizar_extracto_bancario(
    archivo,
    contrasena=None
):

    texto = extraer_texto_pdf(
        archivo,
        contrasena
    )

    es_extracto = validar_extracto_bancario(
        texto
    )

    return {
        "es_extracto": es_extracto,
        "texto": texto
    }
