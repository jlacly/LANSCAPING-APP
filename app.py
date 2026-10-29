import os
import pandas as pd
import streamlit as st

# Archivo local donde se guardan los datos en la nube
DATA_FILE = "registro_maquinas.csv"
LIMITE_ACEITE = 50  # Alerta cada 50 horas

st.set_page_config(
    page_title="Mantenimiento Landscaping", page_icon="🚜", layout="centered"
)
st.title("🚜 Control de Mantenimiento")
st.write("Historial y alertas para tu equipo de Landscaping.")


# Funciones para Cargar y Guardar Datos
def cargar_datos():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(
        columns=["Máquina", "Marca/Modelo", "Horas Actuales", "Último Cambio"]
    )


def guardar_datos(df):
    df.to_csv(DATA_FILE, index=False)


df = cargar_datos()

# --- SISTEMA DE ALERTAS ---
st.subheader("🚨 Alertas de Servicio")
if not df.empty:
    # Asegurar que las columnas sean numéricas antes del cálculo
    df["Horas Actuales"] = pd.to_numeric(df["Horas Actuales"], errors="coerce")
    df["Último Cambio"] = pd.to_numeric(df["Último Cambio"], errors="coerce")

    df["Horas Desde Cambio"] = df["Horas Actuales"] - df["Último Cambio"]
    df["Hrs Restantes"] = LIMITE_ACEITE - df["Horas Desde Cambio"]

    # Filtrar máquinas que necesitan atención urgente
    alertas = df[df["Hrs Restantes"] <= 0]
    if not alertas.empty:
        for idx, row in alertas.iterrows():
            st.error(
                f"⚠️ **{row['Máquina']}** necesita cambio de aceite urgente! (Pasada por {abs(row['Hrs Restantes'])} hrs)"
            )
    else:
        st.success("✅ ¡Todas las máquinas están al día con su aceite!")
else:
    st.info("No hay máquinas registradas aún.")

# --- TABLA DE INVENTARIO ---
st.subheader("📋 Inventario Actual")
if not df.empty:
    # Mostrar tabla simplificada para pantallas de celular
    st.dataframe(
        df[["Máquina", "Horas Actuales", "Último Cambio", "Hrs Restantes"]],
        use_container_width=True,
        hide_index=True,
    )

    # Botón Rápido de Mantenimiento
    st.write("---")
    maquina_mant = st.selectbox(
        "Selecciona máquina para registrar servicio:", df["Máquina"]
    )
    if st.button("🔧 Registrar Cambio de Aceite Hecho Hoy"):
        idx = df[df["Máquina"] == maquina_mant].index
        df.at[idx, "Último Cambio"] = df.at[idx, "Horas Actuales"]
        guardar_datos(df)
        st.toast("¡Mantenimiento guardado!")
        st.rerun()

# --- AGREGAR O ACTUALIZAR MÁQUINA ---
st.write("---")
with st.expander("➕ Registrar Nueva Máquina / Actualizar Horas"):
    nombre = st.text_input("Nombre o ID de la máquina (Ej: Cortacésped 01):")
    marca = st.text_input("Marca / Modelo:")
    horas = st.number_input("Horas actuales de motor:", min_value=0.0, step=1.0)
    aceite = st.number_input(
        "Horas que tenía en su último cambio de aceite:", min_value=0.0, step=1.0
    )

    if st.button("💾 Guardar Equipo"):
        if nombre:
            # Si existe, actualiza; si no, añade
            if nombre in df["Máquina"].values:
                df.loc[
                    df["Máquina"] == nombre,
                    ["Marca/Modelo", "Horas Actuales", "Último Cambio"],
                ] = [marca, horas, aceite]
            else:
                new_row = pd.DataFrame(
                    [[nombre, marca, horas, aceite]], columns=df.columns[:4]
                )
                df = pd.concat([df, new_row], ignore_index=True)
            guardar_datos(df)
            st.success(f"¡{nombre} guardado con éxito!")
            st.rerun()
        else:
            st.warning("Por favor escribe un nombre o ID.")
