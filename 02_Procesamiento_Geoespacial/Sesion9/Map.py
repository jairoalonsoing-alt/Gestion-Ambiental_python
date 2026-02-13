import os
import pandas as pd
import folium

ARCHIVO = "Libro3.csv"
SALIDA = "mapa_brp_davivienda.html"

if not os.path.exists(ARCHIVO):
    raise FileNotFoundError(f"No existe el archivo: {ARCHIVO}")

# ==============================
# LECTURA ROBUSTA (Soporte para ;)
# ==============================
try:
    # Agregamos sep=None y engine='python' para que detecte automáticamente si es , o ; o \t
    df = pd.read_csv(ARCHIVO, sep=None, engine='python', encoding="latin1")
except Exception as e:
    print(f"❌ Error al leer el archivo: {e}")
    exit()

# ==============================
# NORMALIZAR NOMBRES DE COLUMNAS
# ==============================
df.columns = (
    df.columns.astype(str)
      .str.replace("\ufeff", "", regex=False)
      .str.replace("ï»¿", "", regex=False)
      .str.strip()
)

print("✅ Columnas detectadas:", list(df.columns))

# ==============================
# DETECTAR COLUMNA DE CIUDAD
# ==============================
col_ciudad = None
for c in ["Ciudad / Municipio", "CIUDAD", "MUNICIPIO"]:
    if c in df.columns:
        col_ciudad = c
        break

if col_ciudad is None:
    col_ciudad = df.columns[0]
    print(f"⚠️ Usando primera columna como ciudad: {col_ciudad}")

# ==============================
# LIMPIAR Y ASEGURAR COLUMNAS
# ==============================
def limpiar_entero(serie):
    if serie.dtype == 'int64' or serie.dtype == 'float64':
        return serie.fillna(0).astype(int)
    return (
        pd.to_numeric(
            serie.astype(str).str.replace(r"[^\d]", "", regex=True),
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

def encontrar_columna(lista_posibles):
    for c in df.columns:
        if c.strip().upper() in [p.upper() for p in lista_posibles]:
            return c
    return None

# Identificar columnas con los nuevos nombres
col_ret = encontrar_columna(["TOTAL RETIRADOS", "CANTIDAD RETIRADOS", "RETIRADOS"])
col_total = encontrar_columna(["TOTAL BRP", "TOTAL DE BRP", "BRP"])
col_lat = encontrar_columna(["Latitud", "LAT"])
col_lon = encontrar_columna(["Longitud", "LON"])

# --- VALIDACIÓN ---
if col_lat is None or col_lon is None:
    raise KeyError(f"Faltan coordenadas. Detectadas: {list(df.columns)}")

# Asegurar que existan las de negocio
if col_ret is None:
    df["TOTAL RETIRADOS"] = 0
    col_ret = "TOTAL RETIRADOS"

if col_total is None:
    df["TOTAL BRP"] = 0
    col_total = "TOTAL BRP"

# Convertir a numérico
df[col_ret] = limpiar_entero(df[col_ret])
df[col_total] = limpiar_entero(df[col_total])
df[col_lat] = pd.to_numeric(df[col_lat], errors="coerce")
df[col_lon] = pd.to_numeric(df[col_lon], errors="coerce")

# Limpieza final
df = df.dropna(subset=[col_lat, col_lon]).copy()
df = df[df[col_ciudad].astype(str).str.strip().str.lower() != "total general"].copy()

# ==============================
# CREAR MAPA
# ==============================
max_brp = int(df[col_total].max()) if not df.empty and df[col_total].max() > 0 else 10

mapa = folium.Map(location=[4.5, -74], zoom_start=6, tiles="CartoDB positron")

for _, row in df.iterrows():
    val_total = int(row[col_total])
    val_ret = int(row[col_ret])
    
    # Radio dinámico basado en TOTAL BRP
    radius = 6 + (val_total / max_brp) * 25
    
    # Color: Rojo si hay retirados, azul si no
    color = "red" if val_ret > 0 else "blue"
    
    nombre_lugar = str(row[col_ciudad])

    folium.CircleMarker(
        location=[row[col_lat], row[col_lon]],
        radius=radius,
        color=color,
        fill=True,
        fill_opacity=0.6,
        tooltip=f"{nombre_lugar}: BRP {val_total} | Ret {val_ret}",
        popup=folium.Popup(
            f"<b>{nombre_lugar}</b><br>Total BRP: {val_total}<br>Retirados: {val_ret}",
            max_width=300
        )
    ).add_to(mapa)

mapa.save(SALIDA)
print(f"✅ ¡Éxito! Mapa generado en: {os.path.abspath(SALIDA)}")