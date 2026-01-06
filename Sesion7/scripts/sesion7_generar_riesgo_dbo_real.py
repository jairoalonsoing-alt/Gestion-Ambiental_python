import geopandas as gpd
import pandas as pd
import random
import os

print("=== SCRIPT SESION 7 EJECUTANDO ===")

# Rutas
ruta_geojson = "datos/estaciones_calidad_agua_bogota.geojson"
ruta_salida = "resultados/riesgo_ambiental_GIS.csv"

# Leer GEOJSON
print("Leyendo GEOJSON...")
gdf = gpd.read_file(ruta_geojson)

print("Columnas encontradas:")
print(gdf.columns)

# Crear ID si no existe
if "ID_Estacion" not in gdf.columns:
    gdf["ID_Estacion"] = range(1, len(gdf) + 1)

# Extraer coordenadas de la geometría
gdf["coordx"] = gdf.geometry.x
gdf["coordy"] = gdf.geometry.y

# Simular valores reales de DBO (mg/L)
gdf["DBO"] = [random.randint(5, 40) for _ in range(len(gdf))]

# Clasificación de riesgo
def clasificar_riesgo(dbo):
    if dbo < 10:
        return "BAJO"
    elif dbo < 20:
        return "MEDIO"
    else:
        return "ALTO"

gdf["Riesgo_DBO"] = gdf["DBO"].apply(clasificar_riesgo)

# Crear carpeta de resultados si no existe
os.makedirs("resultados", exist_ok=True)

# Exportar CSV completo para ArcGIS
columnas_exportar = ["ID_Estacion", "estacion", "nombre", "rio", "fechacreac",
                     "fechaactua", "coordx", "coordy", "DBO", "Riesgo_DBO"]
gdf[columnas_exportar].to_csv(ruta_salida, index=False)

print("CSV COMPLETO CREADO CORRECTAMENTE")
print(gdf[columnas_exportar].head())