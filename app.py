import os
import pandas as pd
import streamlit as st

# Archivos locales en la nube para guardar datos
MAQUINAS_FILE = "registro_maquinas.csv"
HISTORIAL_FILE = "historial_gastos.csv"
LIMITE_ACEITE = 50  # Alerta cada 50 horas

st.set_page_config(
    page_title="Mantenimiento Landscaping", page_icon="🚜", layout="centered"
)
st.title("🚜 Control de Mantenimiento y Gastos")
st.write("Controla las alertas de servicio y el dinero invertido en tus equipos.")


# --- FUNCIONES DE ALMACENAMIENTO ---
def cargar_maquinas():
    if os.path.exists(MAQUINAS_FILE):
        return pd.read_csv(MAQUINAS_FILE)
    return pd.DataFrame(
        columns=["Máquina", "Marca/Modelo", "Horas Actuales", "Último Cambio"]
    )


def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        return pd.read_csv(HISTORIAL_FILE)
    return pd.DataFrame(
        columns=["Máquina", "Fecha", "Detalle / Pieza", "Costo ($)"]
    )


def guardar_datos(df, filename):
    df.to_csv(filename, index=False)


# Cargar datos actuales
df_maq = cargar_maquinas()
df_hist = cargar_historial()

# --- CÁLCULO DE GASTOS TOTALES POR MÁQUINA ---
gastos_totales = {}
if not df_hist.empty:
    # Asegurar que el costo sea numérico
    df_hist["Costo ($)"] = pd.to_numeric(df_hist["Costo ($)"], errors="coerce")
    # Agrupar la suma de costos por máquina
    gastos_totales = df_hist.groupby("Máquina")["Costo ($)"].sum().to_dict()

# --- SISTEMA DE ALERTAS (ACEITE) ---
st.subheader("🚨 Alertas de Servicio")
if not df_maq.empty:
    df_maq["Horas Actuales"] = pd.to_numeric(
        df_maq["Horas Actuales"], errors="coerce"
    )
    df_maq["Último Cambio"] = pd.to_numeric(
        df_maq["Último Cambio"], errors="coerce"
    )

    df_maq["Horas Desde Cambio"] = (
        df_maq["Horas Actuales"] - df_maq["Último Cambio"]
    )
    df_maq["Hrs Restantes"] = LIMITE_ACEITE - df_maq["Horas Desde Cambio"]

    alertas = df_maq[df_maq["Hrs Restantes"] <= 0]
    if not alertas.empty:
        for idx, row in alertas.iterrows():
            st.error(
                f"⚠️ **{row['Máquina']}** necesita cambio de aceite urgente! (Pasada por {abs(row['Hrs Restantes'])} hrs)"
            )
    else:
        st.success("✅ ¡Todas las máquinas están al día con su aceite!")
else:
    st.info("No hay máquinas registradas aún.")

# --- TABLA DE INVENTARIO Y GASTOS ---
st.subheader("📋 Inventario y Gasto Acumulado")
if not df_maq.empty:
    # Agregar columna de gasto total calculado al inventario visible
    df_maq["Total Gastado ($)"] = df_maq["Máquina"].map(gastos_totales).fillna(0.0)

    st.dataframe(
        df_maq[
            [
                "Máquina",
                "Horas Actuales",
                "Hrs Restantes",
                "Total Gastado ($)",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    # --- SECCIÓN: REGISTRAR MANTENIMIENTO Y GASTO ---
    st.write("---")
    st.subheader("🔧 Registrar Servicio / Gasto de Repuesto")

    maquina_mant = st.selectbox(
        "Selecciona la máquina que recibió el servicio:", df_maq["Máquina"]
    )

    col1, col2 = st.columns(2)
    with col1:
        fecha_serv = st.date_input("Fecha del trabajo:")
        pieza_cambiada = st.text_input(
            "Pieza cambiada / Detalle:",
            placeholder="Ej: Filtro de aire y bujía",
        )
    with col2:
        costo_repuesto = st.number_input(
            "Costo total del repuesto / reparación ($):",
            min_value=0.0,
            step=1.0,
        )
        cambio_aceite_check = st.checkbox(
            "¿Este servicio incluyó Cambio de Aceite?"
        )

    if st.button("🔧 Guardar Servicio y Gasto"):
        if pieza_cambiada:
            # 1. Guardar en el historial de gastos
            nueva_fila_hist = pd.DataFrame(
                [[maquina_mant, str(fecha_serv), pieza_cambiada, costo_repuesto]],
                columns=df_hist.columns[:4],
            )
            df_hist = pd.concat([df_hist, nueva_fila_hist], ignore_index=True)
            guardar_datos(df_hist, HISTORIAL_FILE)

            # 2. Si marcó cambio de aceite, actualizar las horas en el inventario
            if cambio_aceite_check:
                idx = df_maq[df_maq["Máquina"] == maquina_mant].index
                df_maq.at[idx, "Último Cambio"] = df_maq.at[idx, "Horas Actuales"]
                guardar_datos(df_maq, MAQUINAS_FILE)

            st.toast("¡Servicio y gasto registrados correctamente!")
            st.rerun()
        else:
            st.warning("Por favor detalla qué pieza se cambió o el trabajo realizado.")

# --- SECCIÓN: VER HISTORIAL DE BITÁCORA ---
if not df_hist.empty:
    st.write("---")
    with st.expander("📚 Ver Historial Completo de Reparaciones y Notas"):
        st.dataframe(df_hist, use_container_width=True, hide_index=True)

# --- AGREGAR O ACTUALIZAR MÁQUINA ---
st.write("---")
with st.expander("➕ Registrar Nueva Máquina / Actualizar Horas"):
    nombre = st.text_input("Nombre o ID de la máquina (Ej: Toro Z-Master 01):")
    marca = st.text_input("Marca / Modelo:")
    horas = st.number_input(
        "Horas actuales de motor:", min_value=0.0, step=1.0, key="new_hrs"
    )
    aceite = st.number_input(
        "Horas del último cambio de aceite:", min_value=0.0, step=1.0, key="new_oil"
    )

    if st.button("💾 Guardar Equipo"):
        if nombre:
            if nombre in df_maq["Máquina"].values:
                df_maq.loc[
                    df_maq["Máquina"] == nombre,
                    ["Marca/Modelo", "Horas Actuales", "Último Cambio"],
                ] = [marca, horas, aceite]
            else:
                new_row = pd.DataFrame(
                    [[nombre, marca, horas, aceite]], columns=df_maq.columns[:4]
                )
                df_maq = pd.concat([df_maq, new_row], ignore_index=True)
            guardar_datos(df_maq, MAQUINAS_FILE)
            st.success(f"¡{nombre} guardado con éxito!")
            st.rerun()
        else:
            st.warning("Por favor escribe un nombre o ID.")

