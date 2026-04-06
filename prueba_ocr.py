import pytesseract
from PIL import Image
import re

def obtener_total(ruta_imagen):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    imagen = Image.open(ruta_imagen)
    texto = pytesseract.image_to_string(imagen, lang="spa")

    print("Texto detectado:")
    print(texto)

    lineas = texto.split('\n')
    total_encontrado = None

    for linea in lineas:
        linea_mayus = linea.upper()

        # Ignorar cosas que no son total
        if "IVA" in linea_mayus or "AHORRO" in linea_mayus or "CAMBIO" in linea_mayus:
            continue

        # Buscar patrón tipo: T 1,748.00
        match = re.search(r'\bT\s*([\d,]+\.\d{2})', linea)

        if match:
            return match.group(1)

    return "No encontrado"


# USO DEL CÓDIGO
ruta = r"C:\Users\Dimara\OneDrive\Desktop\tickets\ticket.jpg"

total = obtener_total(ruta)

print("TOTAL DETECTADO:")
print(total)