import pandas as pd

datos = pd.read_csv("datos_calidad_agua.csv")

def clasificar(fila):
    if fila["pH"] < 6 or fila["oxigeno_disuelto"] < 6:
        return "Crítico"
    elif fila["turbidez"] > 7:
        return "Regular"
    else:
        return "Bueno"

datos["estado"] = datos.apply(clasificar, axis=1)
datos.to_csv("resultado_calidad_agua.csv", index=False)

print(datos)