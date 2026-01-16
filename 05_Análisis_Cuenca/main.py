import os
import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point
from matplotlib.patches import Patch
import pandas as pd


def main():
    # ===============================
# ======== CONFIGURACIÓN ========
# ===============================
CUENCA_PATH = "data/Cuenca/POMCAS_MADS.shp"
RIOS_PATH = "data/Rios/Drenaje_Doble.shp"
LAT, LON = 4.7110, -74.0721
OUTPUT_FOLDER = "salidas/"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ===============================
# 1. Cargar capas
# ===============================
cuencas = gpd.read_file(CUENCA_PATH)
rios = gpd.read_file(RIOS_PATH)

cuencas = cuencas.to_crs(epsg=3116)
rios = rios.to_crs(epsg=3116)
punto = gpd.GeoDataFrame(
geometry=[Point(LON, LAT)],
crs="EPSG:4326").to_crs(epsg=3116)
cuenca_bogota = cuencas[cuencas.contains(punto.geometry.iloc[0])].copy()

# ===============================
# 2. Zonas urbanas desde OSM
# ===============================
cuenca_wgs = cuenca_bogota.to_crs(epsg=4326)
gdf_urbano = ox.features_from_polygon(
    cuenca_wgs.geometry.iloc[0],
    tags={"landuse": ["residential", "commercial", "industrial"]}
)
gdf_urbano = gdf_urbano[gdf_urbano.geometry.type.isin(["Polygon","MultiPolygon"])]
gdf_urbano = gdf_urbano.explode(index_parts=False).reset_index(drop=True)
gdf_urbano = gdf_urbano.to_crs(epsg=3116)
gdf_urbano["geometry"] = gdf_urbano.buffer(0)

# ===============================
# 3. Recorte de ríos
# ===============================
rios_recortados = gpd.clip(rios, cuenca_bogota)
rios_recortados["geometry"] = rios_recortados.buffer(0)

# ===============================
# 4. ZONIFICACIÓN AMBIENTAL
# ===============================
buffer_cons = gpd.GeoDataFrame(geometry=rios_recortados.buffer(100), crs=cuenca_bogota.crs)
buffer_rec = gpd.GeoDataFrame(geometry=rios_recortados.buffer(500), crs=cuenca_bogota.crs)

buffer_cons = gpd.clip(buffer_cons, cuenca_bogota)
buffer_rec = gpd.clip(buffer_rec, cuenca_bogota)

# Uniones y limpieza
zona_conservacion = gpd.GeoDataFrame(geometry=[buffer_cons.unary_union], crs=cuenca_bogota.crs)
zona_conservacion["geometry"] = zona_conservacion.geometry.buffer(0)

zona_recuperacion_total = gpd.GeoDataFrame(geometry=[buffer_rec.unary_union], crs=cuenca_bogota.crs)
zona_recuperacion_total["geometry"] = zona_recuperacion_total.geometry.buffer(0)

zona_recuperacion = gpd.overlay(zona_recuperacion_total, zona_conservacion, how="difference")
temp = gpd.overlay(cuenca_bogota, zona_recuperacion, how="difference")
zona_uso = gpd.overlay(temp, zona_conservacion, how="difference")

# ===============================
# 5. RIESGO HÍDRICO
# ===============================
gdf_riesgo_alto = gpd.GeoDataFrame(geometry=rios_recortados.buffer(300), crs=cuenca_bogota.crs)
gdf_riesgo_alto["geometry"] = gdf_riesgo_alto.geometry.buffer(0)

gdf_riesgo_medio = gpd.GeoDataFrame(geometry=rios_recortados.buffer(700), crs=cuenca_bogota.crs)
gdf_riesgo_medio["geometry"] = gdf_riesgo_medio.geometry.buffer(0)

zona_riesgo_medio = gpd.overlay(gdf_riesgo_medio, gdf_riesgo_alto, how="difference")
temp = gpd.overlay(cuenca_bogota, zona_riesgo_medio, how="difference")
zona_riesgo_bajo = gpd.overlay(temp, gdf_riesgo_alto, how="difference")

# ===============================
# 6. EXPOSICIÓN URBANA
# ===============================
urbano_alto = gpd.overlay(gdf_urbano, gdf_riesgo_alto, how="intersection")
urbano_medio = gpd.overlay(gdf_urbano, zona_riesgo_medio, how="intersection")
urbano_bajo = gpd.overlay(gdf_urbano, zona_riesgo_bajo, how="intersection")

# Áreas
area_urb_alto = urbano_alto.area.sum()/1e6
area_urb_medio = urbano_medio.area.sum()/1e6
area_urb_bajo = urbano_bajo.area.sum()/1e6
urbano_total_area = gdf_urbano.area.sum()/1e6

# ===============================
# 7. EXPOSICIÓN URBANA POR ZONA
# ===============================
def porcentaje_urbano(zona, urbano, nombre):
    urbano_en_zona = gpd.overlay(urbano, zona, how="intersection")
    area_total = zona.area.sum()/1e6
    area_urb = urbano_en_zona.area.sum()/1e6
    pct = (area_urb/area_total*100) if area_total>0 else 0
    return area_total, area_urb, pct

zonas = {
    "Conservación": zona_conservacion,
    "Recuperación": zona_recuperacion,
    "Uso Controlado": zona_uso
}
resultados = []
for nombre, zona in zonas.items():
    total, urbano_area, pct = porcentaje_urbano(zona, gdf_urbano, nombre)
    resultados.append({"Zona": nombre, "Área total": total, "Área urbana": urbano_area, "% urbano": pct})
df_resultados = pd.DataFrame(resultados)

# ===============================
# 8. EXPORTAR SHAPEFILES Y CSV
# ===============================
zona_conservacion.to_file(OUTPUT_FOLDER+"zona_conservacion.shp")
zona_recuperacion.to_file(OUTPUT_FOLDER+"zona_recuperacion.shp")
zona_uso.to_file(OUTPUT_FOLDER+"zona_uso.shp")
urbano_alto.to_file(OUTPUT_FOLDER+"urbano_riesgo_alto.shp")
urbano_medio.to_file(OUTPUT_FOLDER+"urbano_riesgo_medio.shp")
urbano_bajo.to_file(OUTPUT_FOLDER+"urbano_riesgo_bajo.shp")
df_resultados.to_csv(OUTPUT_FOLDER+"resultados_urbanos.csv", index=False)

# ===============================
# 9. MAPA FINAL CON LEYENDA Y PORCENTAJES
# ===============================
uso_web = zona_uso.to_crs(3857)
rec_web = zona_recuperacion.to_crs(3857)
cons_web = zona_conservacion.to_crs(3857)
cuenca_web = cuenca_bogota.to_crs(3857)
urbano_riesgo_web = urbano_alto.to_crs(3857)
urbano_seguro_web = gpd.overlay(gdf_urbano, urbano_riesgo_web.to_crs(3116), how="difference").to_crs(3857)

fig, ax = plt.subplots(figsize=(11,11))
uso_web.plot(ax=ax, color="#4CAF50", alpha=0.4)
rec_web.plot(ax=ax, color="#FFC107", alpha=0.65)
cons_web.plot(ax=ax, color="#1E88E5", alpha=0.8)
urbano_seguro_web.plot(ax=ax, color="#8E24AA", alpha=0.75)
urbano_riesgo_web.plot(ax=ax, color="#E53935", alpha=0.9)
cuenca_web.boundary.plot(ax=ax, color="black", linewidth=2)

ctx.add_basemap(ax)
ax.legend(handles=[
    Patch(color="#4CAF50", label=f"Uso controlado"),
    Patch(color="#FFC107", label=f"Recuperación"),
    Patch(color="#1E88E5", label=f"Conservación"),
    Patch(color="#8E24AA", label=f"Urbano condicionado"),
    Patch(color="#E53935", label=f"Urbano en riesgo")
], loc="upper left", bbox_to_anchor=(1.02,1))
plt.tight_layout()
ax.set_title("Zonificación Ambiental Integrada – Cuenca del Río Bogotá", fontsize=14)
ax.text(0.99,0.01,f"Elaborado por: Jairo Alonso Porras Bernal\nIngeniero Ambiental\n2026",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"))
plt.show()

# ===============================
# 10. GRÁFICOS AUTOMÁTICOS
# ===============================
# Exposición por riesgo
riesgos = ["Alto","Medio","Bajo"]
areas_riesgo = [area_urb_alto, area_urb_medio, area_urb_bajo]

plt.figure(figsize=(6,4))
plt.bar(riesgos, areas_riesgo, color=["#E53935","#FFC107","#8E24AA"])
plt.ylabel("Área urbana (km²)")
plt.title("Exposición urbana por nivel de riesgo")
for i, v in enumerate(areas_riesgo):
    plt.text(i, v + 0.2, f"{v:.2f} km²", ha="center")
plt.tight_layout()
plt.show()

# Exposición por zona
plt.figure(figsize=(6,4))
plt.bar(df_resultados["Zona"], df_resultados["Área urbana"], color=["#1E88E5","#FFC107","#4CAF50"])
plt.ylabel("Área urbana (km²)")
plt.title("Exposición urbana por zona ambiental")
for i, v in enumerate(df_resultados["Área urbana"]):
    pct = df_resultados["% urbano"].iloc[i]
    plt.text(i, v + 0.2, f"{v:.2f} km²\n({pct:.1f}%)", ha="center")
plt.tight_layout()
plt.show()

if __name__ == "__main__":
    main()

