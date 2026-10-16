import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# Configuración Inicial
st.set_page_config(
    page_title="Control Financiero para Emprendedores",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="expanded",
)


# Configuración de Base de Datos
def init_db():
    conn = sqlite3.connect("control_emprendimiento.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            tipo TEXT,
            categoria TEXT,
            descripcion TEXT,
            monto REAL,
            cantidad INTEGER
        )
    """)
    conn.commit()
    conn.close()


init_db()


def obtener_config(clave, valor_defecto=""):
    conn = sqlite3.connect("control_emprendimiento.db")
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else valor_defecto


def guardar_config(clave, valor):
    conn = sqlite3.connect("control_emprendimiento.db")
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)",
        (clave, valor),
    )
    conn.commit()
    conn.close()


def agregar_movimiento(tipo, categoria, descripcion, monto, cantidad=1):
    conn = sqlite3.connect("control_emprendimiento.db")
    c = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        """
        INSERT INTO movimientos (fecha, tipo, categoria, descripcion, monto, cantidad)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (fecha_actual, tipo, categoria, descripcion, monto, cantidad),
    )
    conn.commit()
    conn.close()


def obtener_movimientos():
    conn = sqlite3.connect("control_emprendimiento.db")
    df = pd.read_sql_query(
        "SELECT * FROM movimientos ORDER BY id DESC", conn
    )
    conn.close()
    return df


# --- CONFIGURACIÓN DE MARCA Y NEGOCIO EN BARRA LATERAL ---
st.sidebar.header("⚙️ Configuración del Negocio")
nombre_negocio_guardado = obtener_config("nombre_negocio", "Mi Emprendimiento")
moneda_guardada = obtener_config("moneda", "$")

nombre_negocio = st.sidebar.text_input(
    "Nombre de tu Negocio:", value=nombre_negocio_guardado
)
moneda = st.sidebar.text_input("Símbolo de Moneda:", value=moneda_guardada)

if (
    nombre_negocio != nombre_negocio_guardado
    or moneda != moneda_guardada
):
    guardar_config("nombre_negocio", nombre_negocio)
    guardar_config("moneda", moneda)
    st.sidebar.success("¡Configuración guardada!")

# --- ENCABEZADO PERSONALIZADO ---
st.title(f"📊 {nombre_negocio}")
st.caption("Gestión financiera y control de caja inteligente")

# --- OBTENER Y CALCULAR FINANZAS ---
df = obtener_movimientos()

if not df.empty:
    total_ventas = df[df["tipo"] == "VENTA"]["monto"].sum()
    total_gastos = df[df["tipo"] == "GASTO"]["monto"].sum()
    ganancia_neta = total_ventas - total_gastos
else:
    total_ventas = 0.0
    total_gastos = 0.0
    ganancia_neta = 0.0

# --- TARJETAS DE MÉTRICAS (TIPO TREINTA) ---
c1, c2, c3 = st.columns(3)
c1.metric("Ventas Totales", f"{moneda} {total_ventas:.2f}")
c2.metric("Compras / Gastos", f"{moneda} {total_gastos:.2f}")
c3.metric(
    "Ganancia Neta",
    f"{moneda} {ganancia_neta:.2f}",
    delta=f"{ganancia_neta:.2f}",
    delta_color="normal",
)

st.divider()

# --- NAVEGACIÓN PRINCIPAL ---
opcion = st.radio(
    "Selecciona una opción:",
    [
        "💵 Registrar Venta",
        "🛒 Registrar Compra/Gasto",
        "📑 Historial de Caja",
        "🧮 Calculadora de Costos",
    ],
    horizontal=True,
)

# 1. REGISTRAR VENTA
if opcion == "💵 Registrar Venta":
    st.subheader("➕ Nueva Venta")
    with st.form("form_venta", clear_on_submit=True):
        producto = st.text_input(
            "Producto / Detalle", placeholder="Ej: Vaso Tres Leches 12 oz"
        )
        cantidad = st.number_input(
            "Cantidad", min_value=1, value=1, step=1
        )
        precio_unitario = st.number_input(
            f"Precio Unitario ({moneda})", min_value=0.0, value=3.50, step=0.50
        )
        total = cantidad * precio_unitario
        st.markdown(f"### Total a cobrar: **{moneda} {total:.2f}**")

        if st.form_submit_button("✅ Guardar Venta"):
            if producto.strip() != "":
                agregar_movimiento(
                    "VENTA",
                    "Venta de Producto",
                    f"{cantidad}x {producto}",
                    total,
                    cantidad,
                )
                st.success(
                    f"¡Venta de {moneda} {total:.2f} registrada exitosamente!"
                )
                st.rerun()
            else:
                st.error("Por favor escribe el nombre del producto.")

# 2. REGISTRAR COMPRA / GASTO
elif opcion == "🛒 Registrar Compra/Gasto":
    st.subheader("➖ Nuevo Gasto o Inversión")
    with st.form("form_gasto", clear_on_submit=True):
        categoria = st.selectbox(
            "Categoría",
            [
                "Materia Prima / Insumos",
                "Empaques y Envoltorios",
                "Servicios / Gas / Luz",
                "Otros Gastos",
            ],
        )
        descripcion = st.text_input(
            "Descripción",
            placeholder="Ej: Compra de latas de leche, vasos, stickers",
        )
        monto_gasto = st.number_input(
            f"Monto Total ({moneda})", min_value=0.0, value=0.0, step=1.0
        )

        if st.form_submit_button("🔴 Registrar Gasto"):
            if monto_gasto > 0 and descripcion.strip() != "":
                agregar_movimiento(
                    "GASTO", categoria, descripcion, monto_gasto, 1
                )
                st.success(
                    f"¡Gasto de {moneda} {monto_gasto:.2f} guardado correctamente!"
                )
                st.rerun()
            else:
                st.error("Ingresa una descripción y un monto válido.")

# 3. HISTORIAL DE CAJA
elif opcion == "📑 Historial de Caja":
    st.subheader("Movimientos Registrados")
    if not df.empty:
        st.dataframe(
            df[["fecha", "tipo", "categoria", "descripcion", "monto"]],
            use_container_width=True,
        )
    else:
        st.info("Aún no hay transacciones registradas.")

# 4. CALCULADORA DE COSTOS
elif opcion == "🧮 Calculadora de Costos":
    st.subheader("Estructura de Costos por Producción")
    costo_lote = st.number_input(
        f"Inversión Total del Lote ({moneda})", value=50.0, step=1.0
    )
    unidades_producidas = st.number_input(
        "Unidades Producidas", value=30, step=1
    )

    costo_unitario = (
        costo_lote / unidades_producidas if unidades_producidas > 0 else 0
    )
    st.info(f"**Costo Directo por Unidad:** {moneda} {costo_unitario:.2f}")

    precio_venta = st.number_input(
        f"Precio de Venta Sugerido ({moneda})", value=3.50, step=0.25
    )
    ganancia_unidad = precio_venta - costo_unitario
    unidades_para_recuperar = (
        int(costo_lote / precio_venta) + 1 if precio_venta > 0 else 0
    )

    ca, cb = st.columns(2)
    ca.metric("Ganancia x Unidad", f"{moneda} {ganancia_unidad:.2f}")
    cb.metric("Vender para Recuperar", f"{unidades_para_recuperar} unidades")
