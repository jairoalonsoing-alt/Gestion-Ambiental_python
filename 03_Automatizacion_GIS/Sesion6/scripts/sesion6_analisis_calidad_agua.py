import pandas as pd
from pathlib import Path

# Ruta base del script
BASE_DIR = Path(__file__).resolve().parent

# Ruta al CSV
ruta_csv = BASE_DIR.parent / "datos" / "calidad_agua.csv"

df = pd.read_csv(ruta_csv)

print("Datos cargados:")
print(df)

# 2. Estadísticas básicas
print("\nEstadísticas generales:")
print(df.describe())

# 3. Función de clasificación ambiental
def riesgo_dbo(dbo):
    if dbo < 20:
        return "BAJO"
    elif dbo < 40:
        return "MEDIO"
    else:
        return "ALTO"

# 4. Aplicar clasificación
df["Riesgo_DBO"] = df["DBO"].apply(riesgo_dbo)

print("\nClasificación de riesgo:")
print(df)

# 5. Exportar resultados para SIG (ruta segura)
ruta_resultados = BASE_DIR.parent / "resultados"
ruta_resultados.mkdir(exist_ok=True)

ruta_salida = ruta_resultados / "riesgo_ambiental_GIS.csv"
df.to_csv(ruta_salida, index=False)

print("\nArchivo exportado en:", ruta_salida)