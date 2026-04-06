import streamlit as st
import json
import os
import matplotlib.pyplot as plt
import datetime
import ocr


USUARIOS_ARCHIVO = "usuarios.json"

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Mis Finanzas", page_icon="💰", layout="wide")

if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None


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


def asegurar_datos(usuario):
    if usuario not in usuarios:
        return {"ingresos": [], "gastos": []}

    if "datos" not in usuarios[usuario]:
        usuarios[usuario]["datos"] = {
            "ingresos": [],
            "gastos": []
        }

    return usuarios[usuario]["datos"]

    datos = usuarios[usuario]["datos"]

    if "ingresos" not in datos:
        datos["ingresos"] = []

    if "gastos" not in datos:
        datos["gastos"] = []

    if "tickets" not in datos:
        datos["tickets"] = []

    return datos


usuarios = cargar_usuarios()

# ---------------- LOGIN ----------------
if st.session_state.usuario_actual is None:

    st.title("🔐 Sistema de Usuarios")

    opcion = st.radio(
        "Selecciona opción",
        ["Login", "Registro", "Olvidé contraseña"]
    )

    correo = st.text_input("Correo")
    password = st.text_input("Contraseña", type="password")

    acepta = st.checkbox("✅ Acepto términos")

    # -------- LOGIN --------
    if opcion == "Login":
        if st.button("Ingresar"):

            if correo in usuarios and usuarios[correo]["password"] == password:
                st.session_state.usuario_actual = correo
                st.success("Bienvenido ✅")
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

    # -------- REGISTRO --------
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

    # -------- RECUPERAR --------
    elif opcion == "Olvidé contraseña":

        st.subheader("🔑 Recuperar contraseña")

        if correo in usuarios:

            nueva = st.text_input("Nueva contraseña", type="password")
            confirmar = st.text_input("Confirmar contraseña", type="password")

            if st.button("Guardar"):

                if nueva != confirmar:
                    st.error("No coinciden")
                elif nueva == "":
                    st.warning("Vacía no")
                else:
                    usuarios[correo]["password"] = nueva
                    guardar_usuarios(usuarios)
                    st.success("Actualizada 🎉")

        else:
            st.warning("Correo no registrado")

    st.stop()


# ---------------- USUARIO ACTIVO ----------------
if "usuario_actual" not in st.session_state or st.session_state.usuario_actual is None:
    st.warning("Debes iniciar sesión")
    st.stop()
    
usuario = st.session_state.usuario_actual
if usuario not in usuarios:
    st.error("Usuario inválido, vuelve a iniciar sesión")
    st.session_state.usuario_actual = None
    st.rerun()

datos = asegurar_datos(usuario)

st.sidebar.write(f"👤 {usuario}")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario_actual = None
    st.rerun()

st.title("💰 Mis Finanzas")
st.success(f"Bienvenido {usuario} 👋")

menu = st.sidebar.selectbox("Menú", [
    "📊 Resumen",
    "💵 Ingresos",
    "💸 Gastos",
    "📋 Movimientos",
    "📸 Tickets",
    "🧾 Ver tickets"
])

st.sidebar.divider()

st.sidebar.divider()

st.sidebar.write("⚠️ Zona peligrosa")

confirmar = st.sidebar.checkbox("Confirmo que quiero eliminar mi cuenta")

if st.sidebar.button("🗑️ Eliminar cuenta"):
    if not confirmar:
        st.sidebar.warning("Debes confirmar primero")
    else:
        if usuario in usuarios:
            del usuarios[usuario]
            guardar_usuarios(usuarios)

        st.session_state.usuario_actual = None
        st.success("Cuenta eliminada correctamente")
        st.rerun()


# ---------------- RESUMEN ----------------
if menu == "📊 Resumen":

    total_ingresos = sum(i["monto"] for i in datos["ingresos"])
    total_gastos = sum(g["monto"] for g in datos["gastos"])
    balance = total_ingresos - total_gastos

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Ingresos", f"${total_ingresos:,.2f}")
    col2.metric("💸 Gastos", f"${total_gastos:,.2f}")
    col3.metric("📈 Balance", f"${balance:,.2f}")

    fig, ax = plt.subplots()
    ax.bar(["Ingresos", "Gastos"], [total_ingresos, total_gastos])
    st.pyplot(fig)


# ---------------- INGRESOS ----------------
if menu == "💵 Ingresos":

    st.subheader("Agregar ingreso")

    fecha = st.date_input("Fecha", value=datetime.date.today())
    desc = st.text_input("Descripción")
    monto = st.number_input("Monto", min_value=0.0)

    if st.button("Guardar ingreso"):
        if desc:
            datos["ingresos"].append({
                "descripcion": desc,
                "monto": monto,
                "fecha": fecha.strftime("%Y-%m-%d")
            })
            guardar_usuarios(usuarios)
            st.success("Ingreso guardado")


# ---------------- GASTOS ----------------
if menu == "💸 Gastos":

    st.subheader("Agregar gasto")

    fecha = st.date_input("Fecha", value=datetime.date.today())
    monto = st.number_input("Monto", min_value=0.0)

    st.write("📂 Selecciona categoría:")

    categorias = {
        "🍔 Comida": "#FF6B6B",
        "👕 Ropa": "#4D96FF",
        "🎓 Escuela": "#6BCB77",
        "💊 Medicamentos": "#FFD93D",
        "💼 Trabajo": "#9D4EDD",
        "👶 Bebé": "#FF8FAB",
        "👨‍👩‍👧 Hijos": "#38B000",
        "🧸 Juguetes": "#F77F00",
        "🏠 Hogar": "#577590",
        "➕ Otro": "#ADB5BD"
    }

    cols = st.columns(2)

    for i, (cat, color) in enumerate(categorias.items()):
        with cols[i % 2]:
            if st.button(cat, key=f"cat_{i}"):
                st.session_state.categoria_temp = cat

            st.markdown(
                f"<div style='height:5px;background:{color};border-radius:5px'></div>",
                unsafe_allow_html=True
            )

    # 👇 obtener categoría seleccionada
    categoria = st.session_state.get("categoria_temp", None)

    st.write("Seleccionado:", categoria if categoria else "Ninguno")

    if st.button("Guardar gasto"):

        if not categoria:
            st.warning("Selecciona una categoría")
            st.stop()

        if monto <= 0:
            st.warning("Monto inválido")
            st.stop()

        # 🎨 obtener color de la categoría
        color = categorias.get(categoria, "#FFFFFF")

        # 👇 guardar gasto con color
        datos["gastos"].append({
            "categoria": categoria,
            "monto": monto,
            "fecha": fecha.strftime("%Y-%m-%d"),
            "color": color
        })

        guardar_usuarios(usuarios)

        # 👇 limpiar selección (opcional pero pro)
        st.session_state.pop("categoria_temp", None)

        st.success("Gasto guardado 💸")
# ---------------- TICKETS ----------------
if menu == "📸 Tickets":

    import uuid

    st.subheader("🧾 Escanear ticket")

    imagen = st.file_uploader("Sube imagen", type=["jpg", "png", "jpeg"])

    if imagen:

        st.image(imagen)

        ruta = "temp.jpg"
        with open(ruta, "wb") as f:
            f.write(imagen.getbuffer())

        total = ocr.obtener_total(ruta)

        st.info(f"Detectado: ${total}")

        total_final = st.number_input("Confirmar total", value=float(total or 0))

        # 👇 elegir fecha
        fecha_ticket = st.date_input("Fecha del ticket", value=datetime.date.today())

        if st.button("Guardar ticket"):

            os.makedirs("tickets", exist_ok=True)

            nombre = f"tickets/{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"

            with open(nombre, "wb") as f:
                f.write(imagen.getbuffer())

            # 🔥 ID único para conectar ticket y gasto
            ticket_id = str(uuid.uuid4())

            # 👇 guardar ticket
            datos.setdefault("tickets", []).append({
                "id": ticket_id,
                "imagen": nombre,
                "total": total_final,
                "fecha": fecha_ticket.strftime("%Y-%m-%d")
            })

            # 👇 guardar también como gasto (con mismo ID)
            datos["gastos"].append({
                "id": ticket_id,
                "categoria": "Ticket escaneado",
                "monto": total_final,
                "fecha": fecha_ticket.strftime("%Y-%m-%d"),
                "color": "#ADB5BD"
            })

            guardar_usuarios(usuarios)

            st.success("Ticket guardado 📸")

# ---------------- VER TICKETS ----------------
if menu == "🧾 Ver tickets":

    st.subheader("🧾 Historial de tickets")

    tickets = datos.get("tickets", [])

    if len(tickets) == 0:
        st.info("No hay tickets guardados")
    else:

        # 👇 filtro por fecha
        fecha_filtro = st.date_input("Filtrar por fecha (opcional)", value=None)

        for i, t in enumerate(tickets):

            # 👇 aplicar filtro
            if fecha_filtro:
                if t["fecha"] != fecha_filtro.strftime("%Y-%m-%d"):
                    continue

            st.write(f"📅 {t['fecha']}")
            st.write(f"💰 ${t['total']}")

            st.image(t["imagen"], width=250)

            col1, col2 = st.columns(2)

            # 👇 eliminar ticket + gasto relacionado
            with col1:
                if st.button(f"🗑️ Eliminar_{i}"):

                    ticket_id = t.get("id")

                    # eliminar ticket
                    tickets.pop(i)

                    # eliminar gasto relacionado
                    datos["gastos"] = [
                        g for g in datos["gastos"]
                        if g.get("id") != ticket_id
                    ]

                    guardar_usuarios(usuarios)
                    st.rerun()

            st.divider()

# ---------------- MOVIMIENTOS ----------------
if menu == "📋 Movimientos":

    st.subheader("Historial")

    for i in datos["ingresos"]:
        st.success(f"💵 {i['descripcion']} - ${i['monto']:,.2f}")

    for g in datos["gastos"]:
        st.error(f"💸 {g['categoria']} - ${g['monto']:,.2f}")
        
        
