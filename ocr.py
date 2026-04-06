import pytesseract
from PIL import Image
import re

def detectar_tienda(texto):

    texto_mayus = texto.upper()

    if "SAMS" in texto_mayus or "SAM'S" in texto_mayus or "SAM" in texto_mayus:
        return "SAMS"

    if "WALMART" in texto_mayus:
        return "WALMART"

    if "OXXO" in texto_mayus:
        return "OXXO"

    return "DESCONOCIDO"


def obtener_total(ruta_imagen):

    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    imagen = Image.open(ruta_imagen)
    texto = pytesseract.image_to_string(imagen, lang="spa")

    tienda = detectar_tienda(texto)

    lineas = texto.split('\n')

    for linea in lineas:
        linea_mayus = linea.upper()

        # ❌ ignorar ruido
        if any(x in linea_mayus for x in ["IVA", "AHORRO", "CAMBIO"]):
            continue

        # 🛒 SAMS (usa T)
        if tienda == "SAMS":
            match = re.search(r'\bT\s*([\d,]+\.\d{2})', linea)
            if match:
                return float(match.group(1).replace(",", ""))

        # 🛒 WALMART (usa TOTAL)
        if tienda == "WALMART":
            if "TOTAL" in linea_mayus:
                match = re.search(r'([\d,]+\.\d{2})', linea)
                if match:
                    return float(match.group(1).replace(",", ""))

        # 🛒 OXXO (TOTAL A PAGAR)
        if tienda == "OXXO":
            if "TOTAL" in linea_mayus:
                match = re.search(r'([\d,]+\.\d{2})', linea)
                if match:
                    return float(match.group(1).replace(",", ""))

        # 🔥 fallback general
        match = re.search(r'\bT\s*([\d,]+\.\d{2})', linea)
        if match:
            return float(match.group(1).replace(",", ""))

    return None