#1️⃣ Importar Pandas
import pandas as pd

#2️⃣ Crear una función ambiental
def riesgo_hidrico(promedio):
    if promedio < 10:
        return "BAJO"
    elif promedio < 20:
        return "MEDIO"
    else:
        return "ALTO"


def riesgo_ambiental(precip, pendiente, uso):
    if precip > 20 and pendiente > 20:
        return "ALTO"
    elif uso == "Urbano" and precip > 15:
        return "ALTO"
    elif precip > 10 and pendiente > 10:
        return "MEDIO"
    else:
        return "BAJO"


def codigo_riesgo(riesgo):
    if riesgo == "BAJO":
        return 1
    elif riesgo == "MEDIO":
        return 2
    else:
        return 3

#3️⃣ Crear datos simulados de estaciones
datos = {
    "Estacion": ["A", "B", "C", "D"],
    "Precipitacion_mm": [8, 15, 22, 30],
    "Pendiente_pct": [5, 12, 25, 40],
    "Uso_suelo": ["Bosque", "Agricola", "Agricola", "Urbano"]
}

def riesgo_ambiental(precip, pendiente, uso):
    if precip > 20 and pendiente > 20:
        return "ALTO"
    elif uso == "Urbano" and precip > 15:
        return "ALTO"
    elif precip > 10 and pendiente > 10:
        return "MEDIO"
    else:
        return "BAJO"

#4️⃣ Crear el DataFrame
df = pd.DataFrame(datos)
df["ID_Estacion"] = range(1, len(df) + 1)

df["Riesgo_Ambiental"] = df.apply(
    lambda x: riesgo_ambiental(
        x["Precipitacion_mm"],
        x["Pendiente_pct"],
        x["Uso_suelo"]
    ),
    axis=1
)

df["Riesgo_Cod"] = df["Riesgo_Ambiental"].apply(codigo_riesgo)

#5️⃣ Calcular promedio general
promedio = df["Precipitacion_mm"].mean()
print("\nPromedio de precipitación:", promedio)

#6️⃣ Clasificar riesgo por estación
df["Riesgo_Ambiental"] = df.apply(
    lambda x: riesgo_ambiental(
        x["Precipitacion_mm"],
        x["Pendiente_pct"],
        x["Uso_suelo"]
    ),
    axis=1
)

df["Riesgo_Cod"] = df["Riesgo_Ambiental"].apply(codigo_riesgo)

print("\nClasificación de riesgo ambiental:")
print(df)

#7️⃣ Exportar a CSV
df.to_csv("riesgo_hidrico_estaciones.csv", index=False)
print("\nArchivo CSV exportado correctamente")

#8️⃣ Leer el CSV exportado
print("\nLeyendo archivo CSV...")

df2 = pd.read_csv("riesgo_hidrico_estaciones.csv")
print(df2)

#9️⃣ Filtrar estaciones con riesgo ALTO
riesgo_alto = df2[df2["Riesgo_Ambiental"] == "ALTO"]

print("\nEstaciones con riesgo hídrico ALTO:")
print(riesgo_alto)

#🔟 Guardar solo estaciones críticas
riesgo_alto.to_csv("estaciones_riesgo_alto.csv", index=False)
print("\nArchivo estaciones_riesgo_alto.csv creado")

df.to_csv("riesgo_ambiental_GIS.csv", index=False)
print("\nArchivo riesgo_ambiental_GIS.csv listo para ArcGIS")