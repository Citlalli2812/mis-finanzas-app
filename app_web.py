import streamlit as st
import json
import os
import matplotlib.pyplot as plt
import datetime 
import requests
import re

USUARIOS_ARCHIVO = "usuarios.json"


# ---------------- CONFIG ----------------
st.set_page_config(page_title="Mis Finanzas", page_icon="💰", layout="wide")

if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None

if "cat" not in st.session_state:
    st.session_state.cat = None

if "ticket" not in st.session_state:
    st.session_state.ticket = None

# ---------------- FUNCIONES ----------------
def cargar_usuarios():
    if not os.path.exists(USUARIOS_ARCHIVO):
        return {}
    try:
        with open(USUARIOS_ARCHIVO, "r") as f:
            return json.load(f)
    except:
        return {}

def guardar_usuarios(usuarios):
    with open(USUARIOS_ARCHIVO, "w") as f:
        json.dump(usuarios, f, indent=4)

def asegurar_datos(usuario, usuarios):
    if usuario not in usuarios:
        usuarios[usuario] = {"password": "", "datos": {}}

    if "datos" not in usuarios[usuario]:
        usuarios[usuario]["datos"] = {}

    datos = usuarios[usuario]["datos"]

    if "ingresos" not in datos:
        datos["ingresos"] = []
    if "gastos" not in datos:
        datos["gastos"] = []
    if "tickets" not in datos:
        datos["tickets"] = []

    return datos

def reducir_imagen(imagen):
    from PIL import Image
    import io

    img = Image.open(imagen)

    # 🔧 Convertir a RGB (por si es PNG raro)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # 🔧 Redimensionar si es muy grande
    max_size = (1024, 1024)
    img.thumbnail(max_size)

    # 🔧 Guardar comprimida
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=70)
    buffer.seek(0)

    return buffer

def leer_ticket(imagen):
    import requests

    try:
        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={
                "file": ("ticket.jpg", imagen, "image/jpeg")
            },
            data={
                "apikey": st.secrets["OCR_API_KEY"],
                "language": "spa",
                "isOverlayRequired": False,
                "OCREngine": 2,
                "scale": True
            },
            timeout=40
        )

        result = response.json()

        # VER RESPUESTA EN APP
        st.write("Respuesta OCR:", result)

        if result.get("IsErroredOnProcessing") == True:
            return ""

        if "ParsedResults" in result and len(result["ParsedResults"]) > 0:
            return result["ParsedResults"][0].get("ParsedText", "")

        return ""

    except Exception as e:
        st.error(f"Error OCR: {e}")
        return ""

def extraer_datos(texto):
    import re
    import datetime

    if not texto:
        return "Desconocido", str(datetime.date.today()), 0.0

    texto_original = texto
    texto = texto.upper()

    lineas = texto_original.split("\n")
    lineas_limpias = [x.strip() for x in lineas if x.strip() != ""]

    total = 0.0
    negocio = "Desconocido"
    fecha = str(datetime.date.today())

    # NEGOCIO AUTOMÁTICO (México)
    # ==================================================

    if "OXXO" in texto:
        negocio = "OXXO"

    elif "WALMART" in texto:
        negocio = "Walmart"

    elif "SORIANA" in texto:
        negocio = "Soriana"

    elif "FARMACIAS GUADALAJARA" in texto or "GUADALAJARA" in texto:
        negocio = "Farmacias Guadalajara"

    elif "COSTCO" in texto:
        negocio = "Costco"

    elif "AMAZON" in texto:
        negocio = "Amazon"

    elif "MERCADO PAGO" in texto:
        negocio = "Mercado Pago"

    elif "SPEI" in texto:
        negocio = "Transferencia SPEI"

    elif "SAMS" in texto or "SAM'S" in texto or "SAMS CLUB" in texto:
        negocio = "Sam's Club"

    elif len(lineas_limpias) > 0:
        negocio = lineas_limpias[0]

    # FECHA
    # ==================================================

    fecha_match = re.search(r"(\d{2})/(\d{2})/(\d{4})", texto_original)

    if fecha_match:
        dia = fecha_match.group(1)
        mes = fecha_match.group(2)
        anio = fecha_match.group(3)
        fecha = f"{anio}-{mes}-{dia}"

    else:
        fecha_match2 = re.search(r"(\d{2})-(\d{2})-(\d{4})", texto_original)

        if fecha_match2:
            dia = fecha_match2.group(1)
            mes = fecha_match2.group(2)
            anio = fecha_match2.group(3)
            fecha = f"{anio}-{mes}-{dia}"

    # TOTAL INTELIGENTE
    # ==================================================

    palabras_total = [
        "TOTAL",
        "VALOR PAG",
        "IMPORTE",
        "PAGADO",
        "MONTO",
        "TOTAL A PAGAR",
        "TOTAL MXN",
        "PAGO"
    ]

    for linea in lineas_limpias:

        linea_upper = linea.upper()

        if any(p in linea_upper for p in palabras_total):

            numeros = re.findall(
                r"\d{1,3}(?:,\d{3})*\.\d{2}|\d+\.\d{2}",
                linea
            )

            for n in numeros:
                try:
                    valor = float(n.replace(",", ""))

                    if valor > total and valor > 1:
                        total = valor
                except:
                    pass

    # RESPALDO SI NO ENCONTRÓ TOTAL
    # ==================================================

    if total == 0:

        numeros = re.findall(
            r"\d{1,3}(?:,\d{3})*\.\d{2}|\d+\.\d{2}",
            texto_original
        )

        for n in numeros:
            try:
                valor = float(n.replace(",", ""))

                if valor > total and valor > 1:
                    total = valor
            except:
                pass

    return negocio, fecha, total

    # ---------------- NEGOCIO ----------------
    if len(lineas) > 0:
        negocio = lineas[0]

    # ---------------- FECHA ----------------
    fecha_match = re.search(r"(\d{2})/(\d{2})/(\d{4})", texto)

    if fecha_match:
        dia = fecha_match.group(1)
        mes = fecha_match.group(2)
        anio = fecha_match.group(3)
        fecha = f"{anio}-{mes}-{dia}"

    # ---------------- TOTAL PRIORIDAD 1 ----------------
    match_valor = re.search(
        r"VALOR\s*PAG\.?\s*\$?\s*([\d,]+\.\d{2})",
        texto,
        re.IGNORECASE
    )

    if match_valor:
        total = float(match_valor.group(1).replace(",", ""))

    else:

        # ---------------- TOTAL PRIORIDAD 2 ----------------
        for linea in lineas:
            if any(p in linea.lower() for p in [
                "total", "importe", "monto", "pagado"
            ]):

                numeros = re.findall(
                    r"\d{1,3}(?:,\d{3})*\.\d{2}|\d+\.\d{2}",
                    linea
                )

                for n in numeros:
                    try:
                        valor = float(n.replace(",", ""))

                        # ignorar montos basura
                        if valor > total and valor > 1:
                            total = valor
                    except:
                        pass

    return negocio, fecha, total
# ---------------- DATOS ----------------
usuarios = cargar_usuarios()

# ---------------- LOGIN ----------------
if st.session_state.usuario_actual is None:

    st.title("🔐 Sistema de Usuarios")

    opcion = st.radio("Selecciona opción", ["Login", "Registro", "Olvidé contraseña"])

    correo = st.text_input("Correo")
    password = st.text_input("Contraseña", type="password")

    acepta = st.checkbox("Acepto términos y políticas")

    # ---------------- LOGIN ----------------
    if opcion == "Login":
        if st.button("Ingresar"):
            if not acepta:
                st.warning("Debes aceptar términos")
            elif correo in usuarios and usuarios[correo]["password"] == password:
                st.session_state.usuario_actual = correo
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

    # ---------------- REGISTRO ----------------
    elif opcion == "Registro":
        if st.button("Crear cuenta"):
            if correo in usuarios:
                st.error("Usuario ya existe")
            else:
                usuarios[correo] = {
                    "password": password,
                    "datos": {
                        "ingresos": [],
                        "gastos": [],
                        "tickets": []
                    }
                }
                guardar_usuarios(usuarios)
                st.success("Cuenta creada")
                st.rerun()

    # ---------------- RECUPERAR CONTRASEÑA ----------------
    elif opcion == "Olvidé contraseña":

        st.subheader("🔑 Recuperar contraseña")

        if correo in usuarios:

            nueva = st.text_input("Nueva contraseña", type="password")
            confirmar = st.text_input("Confirmar contraseña", type="password")

            if st.button("Actualizar contraseña"):

                if nueva != confirmar:
                    st.error("Las contraseñas no coinciden")
                elif nueva == "":
                    st.warning("No puede estar vacía")
                else:
                    usuarios[correo]["password"] = nueva
                    guardar_usuarios(usuarios)
                    st.success("Contraseña actualizada 🎉")

        else:
            st.warning("Correo no registrado")

    st.stop()
# ---------------- USUARIO ----------------
usuario = st.session_state.usuario_actual
datos = asegurar_datos(usuario, usuarios)

st.sidebar.write(f"👤 {usuario}")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario_actual = None
    st.rerun()

# ELIMINAR CUENTA
st.sidebar.write("⚠️ Zona peligrosa")
confirmar = st.sidebar.checkbox("Confirmo eliminar cuenta")

if st.sidebar.button("🗑️ Eliminar cuenta"):
    if confirmar:
        del usuarios[usuario]
        guardar_usuarios(usuarios)
        st.session_state.usuario_actual = None
        st.rerun()

menu = st.sidebar.selectbox("Menú", [
    "📊 Resumen","💵 Ingresos","💸 Gastos","📋 Movimientos","📸 Tickets","🧾 Ver tickets"
])

# ---------------- RESUMEN ----------------
if menu == "📊 Resumen":

    st.subheader("📊 Resumen general")

    total_ingresos = sum(i["monto"] for i in datos["ingresos"])
    total_gastos = sum(g["monto"] for g in datos["gastos"])

    col1, col2 = st.columns(2)
    col1.metric("💰 Ingresos", f"${total_ingresos}")
    col2.metric("💸 Gastos", f"${total_gastos}")

    fig, ax = plt.subplots()
    ax.bar(["Ingresos","Gastos"], [total_ingresos,total_gastos])
    st.pyplot(fig)

    st.divider()

    # 🔴 FILTRO GASTOS
    st.write("🔍 Quiero ver mis gastos")

    fecha_gasto = st.date_input("Fecha gastos", key="fecha_gasto")
    
    if st.button("Buscar gastos"):
        fecha_str = fecha_gasto.strftime("%Y-%m-%d")

        encontrados = [g for g in datos["gastos"] if g["fecha"] == fecha_str]

        if len(encontrados) == 0:
            st.warning("No hay gastos en esa fecha")
        else:
            for g in encontrados:
                st.error(f"{g['categoria']} - ${g['monto']}")

    st.divider()

    # 🟢 FILTRO INGRESOS
    st.write("🔍 Quiero ver mis ingresos")

    fecha_ingreso = st.date_input("Fecha ingresos", key="fecha_ingreso")

    if st.button("Buscar ingresos"):
        fecha_str = fecha_ingreso.strftime("%Y-%m-%d")

        encontrados = [i for i in datos["ingresos"] if i["fecha"] == fecha_str]

        if len(encontrados) == 0:
            st.warning("No hay ingresos en esa fecha")
        else:
            for i in encontrados:
                st.success(f"{i['descripcion']} - ${i['monto']}")

# ---------------- INGRESOS ----------------
if menu == "💵 Ingresos":

    fecha = st.date_input("Fecha", value=datetime.date.today())
    desc = st.text_input("Descripción")
    monto = st.number_input("Monto", min_value=0.0)

    if st.button("Guardar ingreso"):
        datos["ingresos"].append({
            "descripcion": desc,
            "monto": monto,
            "fecha": fecha.strftime("%Y-%m-%d")
        })
        guardar_usuarios(usuarios)
        st.success("Ingreso guardado")

    st.divider()
    st.subheader("📋 Tus ingresos")

    for i, ingreso in enumerate(datos["ingresos"]):
        col1, col2 = st.columns([4,1])

        with col1:
            st.write(f"{ingreso['descripcion']} - ${ingreso['monto']} - {ingreso['fecha']}")

        with col2:
            if st.button("❌", key=f"del_ingreso_{i}"):
                datos["ingresos"].pop(i)
                guardar_usuarios(usuarios)
                st.rerun()

# ---------------- GASTOS ----------------
if menu == "💸 Gastos":

    fecha = st.date_input("Fecha", value=datetime.date.today())
    monto = st.number_input("Monto", min_value=0.0)

    categorias = {
        "🍔 Comida": "#FF6B6B",
        "👕 Ropa": "#4D96FF",
        "💊 Medicamentos": "#FFD93D",
        "👶 Bebé": "#FF8FAB",
        "👨‍👩‍👧 Niños": "#38B000",
        "🧸 Juguetes": "#F77F00"
    }

    cols = st.columns(2)

    for i, (cat, color) in enumerate(categorias.items()):
        with cols[i % 2]:
            if st.button(cat, key=f"cat_{i}"):
                st.session_state.cat = cat

            st.markdown(f"<div style='height:5px;background:{color}'></div>", unsafe_allow_html=True)

    categoria = st.session_state.get("cat", None)

    if st.button("Guardar gasto"):

        if not categoria:
            st.warning("Selecciona categoría")
            st.stop()

        datos["gastos"].append({
            "categoria": categoria,
            "monto": monto,
            "fecha": fecha.strftime("%Y-%m-%d"),
            "color": categorias[categoria]
        })

        guardar_usuarios(usuarios)
        st.success("Gasto guardado")

    st.divider()
    st.subheader("📋 Tus gastos")

    for i, gasto in enumerate(datos["gastos"]):
        col1, col2 = st.columns([4,1])

        with col1:
            st.write(f"{gasto['categoria']} - ${gasto['monto']} - {gasto['fecha']}")

        with col2:
            if st.button("❌", key=f"del_gasto_{i}"):
                datos["gastos"].pop(i)
                guardar_usuarios(usuarios)
                st.rerun()

# ---------------- MOVIMIENTOS ----------------
if menu == "📋 Movimientos":

    st.subheader("📊 Gastos por categoría")

    if len(datos["gastos"]) == 0:
        st.info("Sin datos")
    else:
        suma = {}
        colores = {}

        for g in datos["gastos"]:
            cat = g["categoria"]
            suma[cat] = suma.get(cat, 0) + g["monto"]
            colores[cat] = g["color"]

        fig, ax = plt.subplots()
        ax.bar(suma.keys(), suma.values(), color=list(colores.values()))
        st.pyplot(fig)

# ---------------- TICKETS ----------------

if menu == "📸 Tickets":

    st.subheader("📸 Escanear Ticket")

    fecha_manual = st.date_input("Fecha", value=datetime.date.today())
    imagen = st.file_uploader("Sube ticket", type=["jpg", "png", "jpeg"])

    if imagen is not None:
        if imagen.size > 5 * 1024 * 1024:
            st.warning("⚠️ Imagen pesada, la optimizaré automáticamente")

    if imagen is not None and st.button("Leer ticket"):

        with st.spinner("Leyendo ticket..."):

            imagen_reducida = reducir_imagen(imagen)
            texto = leer_ticket(imagen_reducida)

            if texto == "":
                st.error("❌ No se pudo leer ticket")

            else:
                # ---------------- NUEVO ----------------
                negocio, fecha_ocr, total = extraer_datos(texto)

                # si OCR no encontró negocio
                if negocio == "":
                    negocio = "Negocio desconocido"

                # si OCR no encontró total correcto
                try:
                    total = float(str(total).replace(",", ""))
                except:
                    total = 0.0

                # usar fecha OCR si existe, si no usar manual
                if fecha_ocr != "":
                    fecha_final = fecha_ocr
                else:
                    fecha_final = fecha_manual.strftime("%Y-%m-%d")
                # --------------------------------------

                st.success("✅ Ticket leído")

                st.session_state.ticket = {
                    "negocio": negocio,
                    "fecha": fecha_final,
                    "total": total
                }

    if "ticket" in st.session_state and st.session_state.ticket is not None:

        t = st.session_state.ticket

        st.divider()
        st.subheader("📝 Confirmar datos")

        negocio = st.text_input("Negocio", value=t["negocio"])
        fecha = st.text_input("Fecha", value=t["fecha"])

        total = st.number_input(
            "Total",
            min_value=0.0,
            value=float(t["total"]),
            step=1.0
        )

        tipo = st.radio("Tipo", ["Gasto", "Ingreso"])

        categoria = st.selectbox(
            "Categoría",
            ["Comida", "Ropa", "Medicamentos"]
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Guardar Ticket"):

                datos["tickets"].append({
                    "negocio": negocio,
                    "fecha": fecha,
                    "total": total,
                    "tipo": tipo,
                    "categoria": categoria
                })

                guardar_usuarios(usuarios)

                st.session_state.ticket = None

                st.success("✅ Ticket guardado")
                st.rerun()

        with col2:
            if st.button("Cancelar"):
                st.session_state.ticket = None
                st.rerun()


# ---------------- VER TICKETS ----------------

if menu == "🧾 Ver tickets":

    st.subheader("🧾 Tickets guardados")

    if len(datos["tickets"]) == 0:
        st.info("No tienes tickets guardados")

    for i, t in enumerate(datos["tickets"]):

        col1, col2 = st.columns([4, 1])

        with col1:
            st.write(f"🏪 {t['negocio']}")
            st.write(f"💰 ${t['total']} - {t['fecha']}")
            st.write(f"📂 {t['categoria']} - {t['tipo']}")
            st.write("---")

        with col2:
            if st.button("❌", key=f"del_ticket_{i}"):

                datos["tickets"].pop(i)
                guardar_usuarios(usuarios)
                st.rerun()