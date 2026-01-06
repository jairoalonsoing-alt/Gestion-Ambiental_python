import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# ---------------------------
# CONFIGURACIÓN
# ---------------------------

st.set_page_config(page_title="Dashboard Ambiental", layout="wide")

st.title("🌱 Dashboard Ambiental – Sesión 3")
st.write("Ingeniero Ambiental — Jairo Alonso Porras Bernal")
st.write("Bogotá, Col")
st.write("+57 300 9489807; jairo.alonso.ing@gmail.com")

# ---------------------------
# CARGA DE DATOS
# ---------------------------

st.header("📂 Indicadores de Calidad del Aire")

data_path = "data"
archivos = os.listdir(data_path)

st.write("Archivos disponibles en /data:")
st.write(archivos)

# =========================
# Cargar calidad del aire
# =========================
if "calidad_aire.csv" in archivos:
    try:
        df_aire = pd.read_csv(
            os.path.join(data_path, "calidad_aire.csv"),
            sep=",",
            encoding="latin-1"
        )

        df_aire.columns = (
            df_aire.columns
            .str.strip()
            .str.lower()
            .str.replace(".", "", regex=False)
        )

        st.success("✔ calidad_aire.csv cargado")
        st.write("Columnas reales en calidad_aire:")
        st.write(list(df_aire.columns))
        st.write(df_aire.head())

        columnas_esperadas = {"pm25", "pm10"}
        if not columnas_esperadas.issubset(df_aire.columns):
            st.error("❌ El archivo calidad_aire.csv no tiene las columnas necesarias")
            st.stop()

    except Exception as e:
        st.error(f"Error cargando calidad_aire.csv: {e}")
        st.stop()
else:
    st.warning("No se encontró calidad_aire.csv")
    st.stop()

# =========================
# Cargar contaminación geo
# =========================
st.header("📂 Calidad de Aire por Ciudad")
if "contaminacion_geo.csv" in archivos:
    try:
        df_geo = pd.read_csv(
            os.path.join(data_path, "contaminacion_geo.csv"),
            sep=";",
            encoding="latin-1"
        )

        # Normalizar columnas
        df_geo.columns = (
            df_geo.columns
            .str.strip()
            .str.lower()
            .str.replace(".", "", regex=False)
        )

        st.success("✔ contaminacion_geo.csv cargado")
        st.write("Columnas detectadas en contaminacion_geo:")
        st.write(list(df_geo.columns))

        columnas_geo = {"lat", "lon", "pm25", "ciudad"}

        if not columnas_geo.issubset(df_geo.columns):
            st.error("❌ contaminacion_geo.csv no tiene columnas geográficas válidas")
            st.stop()

    except Exception as e:
        st.error(f"Error cargando contaminacion_geo.csv: {e}")
        st.stop()
else:
    st.warning("No se encontró contaminacion_geo.csv")
    st.stop()

# ---------------------------
# INDICADORES
# ---------------------------

st.subheader("📊 Indicadores de Calidad del Aire")

col1, col2 = st.columns(2)

with col1:
            st.metric("PM2.5 promedio", round(df_aire["pm25"].mean(), 1))

with col2:
            st.metric("PM10 promedio", round(df_aire["pm10"].mean(), 1))

# ---------------------------
# MAPA
# ---------------------------

st.subheader("🗺️ Mapa de Contaminación")

m = folium.Map(location=[4.6, -74.1], zoom_start=5)

for _, row in df_geo.iterrows():
            folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=8,
        popup=f"{row['ciudad']}<br>PM2.5: {row['pm25']}",
        color="red",
        fill=True,
        fill_opacity=0.7
    ).add_to(m)

st_folium(m, width=900, height=500)