
# -*- coding: utf-8 -*-
import os
import warnings
warnings.filterwarnings("ignore")

import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point
from matplotlib.patches import Patch
import pandas as pd

# ===============================
# ======== CONFIGURACIÓN ========
# ===============================
CUENCA_PATH = "data/Cuenca/POMCAS_MADS.shp"
RIOS_PATH = "data/Rios/Drenaje_Doble.shp"

# Punto de referencia (Bogotá aprox.)
LAT, LON = 4.7110, -74.0721

OUTPUT_FOLDER = "salidas"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# CRS
CRS_GEOG = "EPSG:4326"   # WGS84
CRS_PROJ = "EPSG:3116"   # MAGNA-SIRGAS / Colombia Bogota
CRS_WEB  = "EPSG:3857"   # Web Mercator para mapas base


def fix_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Arregla geometrías inválidas usando buffer(0), ignora nulos."""
    if gdf is None or gdf.empty:
        return gdf
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.buffer(0)
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notnull()]
    return gdf


def safe_overlay(gdf1: gpd.GeoDataFrame, gdf2: gpd.GeoDataFrame, how: str) -> gpd.GeoDataFrame:
    """Overlay seguro que retorna vacío si alguna entrada es vacía."""
    if gdf1 is None or gdf1.empty:
        return gpd.GeoDataFrame(geometry=[], crs=gdf2.crs if gdf2 is not None else None)
    if gdf2 is None or gdf2.empty:
        if how in ("difference",):
            # difference de algo con vacío -> original
            return gdf1.copy()
        elif how in ("intersection",):
            # intersección con vacío -> vacío
            return gpd.GeoDataFrame(geometry=[], crs=gdf1.crs)
        else:
            return gpd.GeoDataFrame(geometry=[], crs=gdf1.crs)
    gdf1 = fix_geometries(gdf1)
    gdf2 = fix_geometries(gdf2)
    if gdf1.empty or gdf2.empty:
        return gpd.GeoDataFrame(geometry=[], crs=gdf1.crs)
    out = gpd.overlay(gdf1, gdf2, how=how)
    return fix_geometries(out)


def project_to(gdf: gpd.GeoDataFrame, epsg: int | str) -> gpd.GeoDataFrame:
    """Proyecta con seguridad si no está en ese CRS."""
    if gdf is None or gdf.empty:
        return gdf
    if gdf.crs is None or gdf.crs.to_string().upper() != f"EPSG:{str(epsg)}":
        return gdf.to_crs(epsg=epsg)
    return gdf


def buffered_union(gdf: gpd.GeoDataFrame, dist: float, crs) -> gpd.GeoDataFrame:
    """Hace buffer por dist y disuelve todo en una sola geometría."""
    if gdf is None or gdf.empty:
        return gpd.GeoDataFrame(geometry=[], crs=crs)
    buf = gdf.buffer(dist)
    geom = gpd.GeoDataFrame(geometry=[buf.unary_union], crs=crs)
    return fix_geometries(geom)


def main():
    # ===============================
    # 1. Cargar capas
    # ===============================
    if not os.path.exists(CUENCA_PATH):
        raise FileNotFoundError(f"No se encontró la capa de cuencas: {CUENCA_PATH}")
    if not os.path.exists(RIOS_PATH):
        raise FileNotFoundError(f"No se encontró la capa de ríos: {RIOS_PATH}")

    cuencas = gpd.read_file(CUENCA_PATH)
    rios = gpd.read_file(RIOS_PATH)

    # Proyección a CRS de trabajo
    cuencas = project_to(cuencas, 3116)
    rios = project_to(rios, 3116)

    # Punto en CRS proyectado
    punto = gpd.GeoDataFrame(geometry=[Point(LON, LAT)], crs=CRS_GEOG)
    punto = project_to(punto, 3116)

    # Selección de cuenca que contiene el punto
    mask = cuencas.contains(punto.geometry.iloc[0])
    if mask.sum() == 0:
        raise ValueError(
            "El punto de referencia no cae dentro de ninguna cuenca del shapefile. "
            "Por favor verifica LAT/LON o la capa de cuencas."
        )
    cuenca_bogota = cuencas.loc[mask].copy()
    cuenca_bogota = fix_geometries(cuenca_bogota)

    # ===============================
    # 2. Zonas urbanas desde OSM
    # ===============================
    cuenca_wgs = project_to(cuenca_bogota, 4326)
    poly = cuenca_wgs.geometry.iloc[0]

    gdf_urbano_wgs = ox.features_from_polygon(
        poly,
        tags={"landuse": ["residential", "commercial", "industrial"]}
    )

    # Solo polígonos
    gdf_urbano_wgs = gdf_urbano_wgs[gdf_urbano_wgs.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()

    # Explode multipolígonos
    if not gdf_urbano_wgs.empty:
        gdf_urbano_wgs = gdf_urbano_wgs.explode(index_parts=False).reset_index(drop=True)

    gdf_urbano = project_to(gdf_urbano_wgs, 3116)
    gdf_urbano = fix_geometries(gdf_urbano)

    # ===============================
    # 3. Recorte de ríos
    # ===============================
    rios_recortados = gpd.clip(rios, cuenca_bogota)
    rios_recortados = fix_geometries(rios_recortados)

    # ===============================
    # 4. ZONIFICACIÓN AMBIENTAL
    # ===============================
    buffer_cons = gpd.GeoDataFrame(geometry=rios_recortados.buffer(100), crs=cuenca_bogota.crs)
    buffer_rec  = gpd.GeoDataFrame(geometry=rios_recortados.buffer(500), crs=cuenca_bogota.crs)
    buffer_cons = gpd.clip(buffer_cons, cuenca_bogota)
    buffer_rec  = gpd.clip(buffer_rec,  cuenca_bogota)

    buffer_cons = fix_geometries(buffer_cons)
    buffer_rec  = fix_geometries(buffer_rec)

    zona_conservacion = buffered_union(buffer_cons, 0, cuenca_bogota.crs)
    zona_recuperacion_total = buffered_union(buffer_rec, 0, cuenca_bogota.crs)

    # Recuperación = (rec_total - conservación)
    zona_recuperacion = safe_overlay(zona_recuperacion_total, zona_conservacion, how="difference")

    # Uso controlado = cuenca - (recuperación U conservación)
    temp = safe_overlay(cuenca_bogota, zona_recuperacion, how="difference")
    zona_uso = safe_overlay(temp, zona_conservacion, how="difference")

    # ===============================
    # 5. RIESGO HÍDRICO
    # ===============================
    gdf_riesgo_alto = buffered_union(rios_recortados, 300, cuenca_bogota.crs)
    gdf_riesgo_medio_total = buffered_union(rios_recortados, 700, cuenca_bogota.crs)
    zona_riesgo_medio = safe_overlay(gdf_riesgo_medio_total, gdf_riesgo_alto, how="difference")

    # Riesgo bajo = cuenca - (alto U medio)
    temp = safe_overlay(cuenca_bogota, zona_riesgo_medio, how="difference")
    zona_riesgo_bajo = safe_overlay(temp, gdf_riesgo_alto, how="difference")

    # ===============================
    # 6. EXPOSICIÓN URBANA
    # ===============================
    if gdf_urbano is None or gdf_urbano.empty:
        urbano_alto = gpd.GeoDataFrame(geometry=[], crs=cuenca_bogota.crs)
        urbano_medio = gpd.GeoDataFrame(geometry=[], crs=cuenca_bogota.crs)
        urbano_bajo = gpd.GeoDataFrame(geometry=[], crs=cuenca_bogota.crs)
    else:
        urbano_alto = safe_overlay(gdf_urbano, gdf_riesgo_alto, how="intersection")
        urbano_medio = safe_overlay(gdf_urbano, zona_riesgo_medio, how="intersection")
        urbano_bajo  = safe_overlay(gdf_urbano, zona_riesgo_bajo,  how="intersection")

    # Áreas (km²)
    area_urb_alto  = (urbano_alto.area.sum() / 1e6) if not urbano_alto.empty else 0.0
    area_urb_medio = (urbano_medio.area.sum() / 1e6) if not urbano_medio.empty else 0.0
    area_urb_bajo  = (urbano_bajo.area.sum()  / 1e6) if not urbano_bajo.empty else 0.0
    urbano_total_area = (gdf_urbano.area.sum() / 1e6) if not gdf_urbano.empty else 0.0

    # ===============================
    # 7. EXPOSICIÓN URBANA POR ZONA
    # ===============================
    def porcentaje_urbano(zona: gpd.GeoDataFrame, urbano: gpd.GeoDataFrame):
        if zona is None or zona.empty:
            return 0.0, 0.0, 0.0
        if urbano is None or urbano.empty:
            area_total = zona.area.sum() / 1e6
            return area_total, 0.0, 0.0
        urbano_en_zona = safe_overlay(urbano, zona, how="intersection")
        area_total = zona.area.sum() / 1e6
        area_urb = urbano_en_zona.area.sum() / 1e6 if not urbano_en_zona.empty else 0.0
        pct = (area_urb / area_total * 100) if area_total > 0 else 0.0
        return area_total, area_urb, pct

    zonas = {
        "Conservación": zona_conservacion,
        "Recuperación": zona_recuperacion,
        "Uso Controlado": zona_uso
    }
    resultados = []
    for nombre, zona in zonas.items():
        total, urbano_area, pct = porcentaje_urbano(zona, gdf_urbano)
        resultados.append({
            "Zona": nombre,
            "Área total (km²)": total,
            "Área urbana (km²)": urbano_area,
            "% urbano": pct
        })
    df_resultados = pd.DataFrame(resultados)

    # ===============================
    # 8. EXPORTAR SHAPEFILES Y CSV
    # ===============================
    def to_file_safe(gdf: gpd.GeoDataFrame, path: str):
        if gdf is not None and not gdf.empty:
            gdf.to_file(path)

    to_file_safe(zona_conservacion, os.path.join(OUTPUT_FOLDER, "zona_conservacion.shp"))
    to_file_safe(zona_recuperacion, os.path.join(OUTPUT_FOLDER, "zona_recuperacion.shp"))
    to_file_safe(zona_uso,           os.path.join(OUTPUT_FOLDER, "zona_uso.shp"))
    to_file_safe(urbano_alto,        os.path.join(OUTPUT_FOLDER, "urbano_riesgo_alto.shp"))
    to_file_safe(urbano_medio,       os.path.join(OUTPUT_FOLDER, "urbano_riesgo_medio.shp"))
    to_file_safe(urbano_bajo,        os.path.join(OUTPUT_FOLDER, "urbano_riesgo_bajo.shp"))
    df_resultados.to_csv(os.path.join(OUTPUT_FOLDER, "resultados_urbanos.csv"), index=False, encoding="utf-8")

    # ===============================
    # 9. MAPA FINAL CON LEYENDA Y PORCENTAJES
    # ===============================
    uso_web  = project_to(zona_uso, 3857)
    rec_web  = project_to(zona_recuperacion, 3857)
    cons_web = project_to(zona_conservacion, 3857)
    cuenca_web = project_to(cuenca_bogota, 3857)
    urbano_riesgo_web = project_to(urbano_alto, 3857)

    # Urbano seguro = urbano - (urbano en riesgo)
    if gdf_urbano is not None and not gdf_urbano.empty:
        urbano_seguro = safe_overlay(gdf_urbano, project_to(urbano_riesgo_web, 3116), how="difference")
        urbano_seguro_web = project_to(urbano_seguro, 3857)
    else:
        urbano_seguro_web = gpd.GeoDataFrame(geometry=[], crs=CRS_WEB)

    fig, ax = plt.subplots(figsize=(11, 11))
    if not uso_web.empty:
        uso_web.plot(ax=ax, color="#4CAF50", alpha=0.4)
    if not rec_web.empty:
        rec_web.plot(ax=ax, color="#FFC107", alpha=0.65)
    if not cons_web.empty:
        cons_web.plot(ax=ax, color="#1E88E5", alpha=0.8)
    if not urbano_seguro_web.empty:
        urbano_seguro_web.plot(ax=ax, color="#8E24AA", alpha=0.75)
    if not urbano_riesgo_web.empty:
        urbano_riesgo_web.plot(ax=ax, color="#E53935", alpha=0.9)
    if not cuenca_web.empty:
        cuenca_web.boundary.plot(ax=ax, color="black", linewidth=2)

    # Basemap
    try:
        ctx.add_basemap(ax, crs=CRS_WEB)
    except Exception:
        pass

    # --- Leyenda dinámica con porcentajes por zona (robusta) ---
    def get_pct(df, zona_nombre):
        try:
            vals = df.loc[df['Zona'] == zona_nombre, '% urbano'].values
            if len(vals) == 0:
                return None
            v = vals[0]
            if pd.isna(v):
                return None
            return float(v)
        except Exception:
            return None

    def label_with_pct(base, p):
        return f"{base} ({p:.1f}%)" if (p is not None) else base

    p_uso  = get_pct(df_resultados, "Uso Controlado")
    p_rec  = get_pct(df_resultados, "Recuperación")
    p_cons = get_pct(df_resultados, "Conservación")

    legend_handles = [
        Patch(color="#4CAF50", label=label_with_pct("Uso controlado", p_uso)),
        Patch(color="#FFC107", label=label_with_pct("Recuperación", p_rec)),
        Patch(color="#1E88E5", label=label_with_pct("Conservación", p_cons)),
        Patch(color="#8E24AA", label="Urbano condicionado"),
        Patch(color="#E53935", label="Urbano en riesgo"),
    ]
    ax.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(1.02, 1))

    ax.set_title("Zonificación Ambiental Integrada – Cuenca del Río Bogotá", fontsize=14)
    ax.text(
        0.99, 0.01,
        "Elaborado por: Jairo Alonso Porras Bernal\nIngeniero Ambiental\n2026",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none")
    )
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, "mapa_zonificacion.png"), dpi=200)
    plt.show()

    # ===============================
    # 10. GRÁFICOS AUTOMÁTICOS
    # ===============================
    # Exposición por riesgo
    riesgos = ["Alto", "Medio", "Bajo"]
    areas_riesgo = [area_urb_alto, area_urb_medio, area_urb_bajo]

    plt.figure(figsize=(6, 4))
    plt.bar(riesgos, areas_riesgo, color=["#E53935", "#FFC107", "#8E24AA"])
    plt.ylabel("Área urbana (km²)")
    plt.title("Exposición urbana por nivel de riesgo")
    altura_texto = (max(areas_riesgo) * 0.02) if (len(areas_riesgo) > 0 and max(areas_riesgo) > 0) else 0.02
    for i, v in enumerate(areas_riesgo):
        plt.text(i, v + altura_texto, f"{v:.2f} km²", ha="center")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, "grafico_exposicion_riesgo.png"), dpi=200)
    plt.show()

    # Exposición por zona
    plt.figure(figsize=(6, 4))
    bar_colors = ["#1E88E5", "#FFC107", "#4CAF50"]  # Cons, Rec, Uso
    plt.bar(df_resultados["Zona"], df_resultados["Área urbana (km²)"], color=bar_colors)
    plt.ylabel("Área urbana (km²)")
    plt.title("Exposición urbana por zona ambiental")
    max_bar = df_resultados["Área urbana (km²)"].max() if not df_resultados.empty else 0
    altura_texto2 = (max_bar * 0.02) if max_bar > 0 else 0.02
    for i, v in enumerate(df_resultados["Área urbana (km²)"]):
        pct = df_resultados["% urbano"].iloc[i]
        plt.text(i, v + altura_texto2, f"{v:.2f} km²\n({pct:.1f}%)", ha="center")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, "grafico_exposicion_zona.png"), dpi=200)
    plt.show()

    # Resumen
    print("\n=== Resumen de áreas (km²) ===")
    print(f"Urbano total (OSM): {urbano_total_area:.2f} km²")
    print(f"Urbano en riesgo ALTO: {area_urb_alto:.2f} km²")
    print(f"Urbano en riesgo MEDIO: {area_urb_medio:.2f} km²")
    print(f"Urbano en riesgo BAJO: {area_urb_bajo:.2f} km²")
    print("\n=== Exposición por zona ===")
    print(df_resultados.to_string(index=False))


if __name__ == "__main__":
    main()