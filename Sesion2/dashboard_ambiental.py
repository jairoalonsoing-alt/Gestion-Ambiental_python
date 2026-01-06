import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Título
st.title("Dashboard Ambiental – Calidad del Aire")
st.markdown("""
### 👨‍🏭 Ingeniero Ambiental — Jairo Alonso Porras Bernal 
Dashboard de Calidad del Aire  
Análisis automatizado de contaminantes atmosféricos

---
""")
# Cargar datos
df = pd.read_csv("calidad_aire.csv")

st.subheader("Datos cargados")
st.dataframe(df)

# Gráfico PM2.5
st.subheader("PM2.5 por día")
fig, ax = plt.subplots()
ax.plot(df["dia"], df["pm25"])
ax.set_xlabel("Día")
ax.set_ylabel("PM2.5 (µg/m³)")
st.pyplot(fig)

# Gráfico PM10
st.subheader("PM10 por día")
fig2, ax2 = plt.subplots()
ax2.plot(df["dia"], df["pm10"])
ax2.set_xlabel("Día")
ax2.set_ylabel("PM10 (µg/m³)")
st.pyplot(fig2)
# --- INDICADORES ---
st.subheader("Indicadores de Calidad del Aire")

col1, col2, col3, col4 = st.columns(4)

col1.metric("PM2.5 Promedio", f"{df['pm25'].mean():.1f} µg/m³")
col2.metric("PM10 Promedio", f"{df['pm10'].mean():.1f} µg/m³")
col3.metric("NO₂ Promedio", f"{df['no2'].mean():.1f} ppb")
col4.metric("SO₂ Promedio", f"{df['so2'].mean():.1f} ppb")
st.subheader("Comparación de contaminantes")

plt.figure(figsize=(10, 4))
plt.plot(df["dia"], df["pm25"], label="PM2.5")
plt.plot(df["dia"], df["pm10"], label="PM10")
plt.plot(df["dia"], df["no2"], label="NO2")
plt.plot(df["dia"], df["so2"], label="SO2")

plt.xlabel("Día")
plt.ylabel("Concentración")
plt.legend()
st.pyplot(plt)

st.subheader("Interpretación según estándares")

def interpretar_pm25(valor):
    if valor <= 15:
        return "Buena"
    elif valor <= 25:
        return "Moderada"
    elif valor <= 50:
        return "Dañina para grupos sensibles"
    else:
        return "Dañina para todos"

def interpretar_pm10(valor):
    if valor <= 50:
        return "Buena"
    elif valor <= 100:
        return "Moderada"
    elif valor <= 150:
        return "Dañina para grupos sensibles"
    else:
        return "Dañina para todos"

pm25_avg = df["pm25"].mean()
pm10_avg = df["pm10"].mean()

st.write(f"**PM2.5 promedio:** {pm25_avg:.1f} → {interpretar_pm25(pm25_avg)}")
st.write(f"**PM10 promedio:** {pm10_avg:.1f} → {interpretar_pm10(pm10_avg)}")
st.subheader("Conclusiones del análisis")

st.markdown(f"""
- El valor promedio de PM2.5 fue **{pm25_avg:.1f} µg/m³**, clasificado como **{interpretar_pm25(pm25_avg)}**.  
- El valor promedio de PM10 fue **{pm10_avg:.1f} µg/m³**, clasificado como **{interpretar_pm10(pm10_avg)}**.  
- Las concentraciones más altas se observaron entre los días **{df['dia'].idxmax()+1}** y **{df['dia'].idxmin()+1}**.
- Se recomienda realizar seguimiento continuo según lineamientos del **IDEAM**.
""")
import folium
from streamlit_folium import st_folium

st.subheader("🗺️ Mapa de Contaminación por Ciudad")

df_map = pd.read_csv("contaminacion_geo.csv")

# Crear mapa con centro en Colombia
m = folium.Map(location=[4.5, -74.1], zoom_start=6)

# Añadir puntos
for _, row in df_map.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=row["pm25"] / 2,
        popup=f"{row['ciudad']} — PM2.5: {row['pm25']}",
        color="red" if row["pm25"] > 30 else "orange",
        fill=True,
    ).add_to(m)

# Mostrar mapa
st_folium(m, width=700, height=450)
from folium.plugins import HeatMap

st.subheader("🔥 Mapa de Calor — PM2.5")

heat_data = df_map[["lat", "lon", "pm25"]].values.tolist()

m2 = folium.Map(location=[4.5, -74.1], zoom_start=6)

HeatMap(heat_data).add_to(m2)

st_folium(m2, width=700, height=450)
import pandas as pd

# Cargar base de datos
df = pd.read_csv("datos_pm25.csv", sep=";", encoding="latin1")
df_map = pd.read_csv("contaminacion_geo.csv", sep=";", encoding="latin1")
df_map.columns = df_map.columns.str.strip().str.lower()

st.write("Columnas detectadas:", df_map.columns.tolist())
st.write("Columnas cargadas:", df.columns.tolist())
df_map = pd.read_csv("contaminacion_geo.csv", sep=";", encoding="latin1")
df_map.columns = ["ciudad", "lat", "lon", "pm25"]
st.write("Columnas cargadas:", df.columns.tolist())
# Limpiar caracteres especiales
df['ciudad'] = df['ciudad'].str.replace("�", "á", regex=False)
df['ciudad'] = df['ciudad'].str.replace("Bogotá", "Bogotá")
df['ciudad'] = df['ciudad'].str.replace("Medellín", "Medellín")

st.write("Datos de calidad del aire")
st.dataframe(df)