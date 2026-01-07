# Función para calcular promedio
def promedio_precipitacion(datos):
    return sum(datos) / len(datos)

# Función para calcular volumen de agua
def volumen_agua(area, prec):
    return area * prec / 1000  # m3

# Función para calcular escorrentía
def escorrentia(vol, coef):
    return vol * coef

# Función para clasificar riesgo hídrico
def riesgo_hidrico(prec):
    if prec < 10:
        return "BAJO"
    elif prec < 20:
        return "MEDIO"
    else:
        return "ALTO"

# --- Programa principal ---

# Ingreso de datos
area = float(input("Área de la cuenca (m2): "))
coeficiente = float(input("Coeficiente de escorrentía (0-1): "))

precipitaciones = []
print("Ingrese la precipitación diaria en mm (0 para terminar):")
prec = float(input(f"Día 1: "))

while prec != 0:
    precipitaciones.append(prec)
    prec = float(input(f"Día {len(precipitaciones)+1}: "))

# Verificar si se ingresaron datos
if len(precipitaciones) == 0:
    print("No se ingresaron datos.")
else:
    # Calcular promedio
    prom = promedio_precipitacion(precipitaciones)
    print("\nPromedio de precipitación:", round(prom,2), "mm")

    # Calcular volumen total y escorrentía
    for i, p in enumerate(precipitaciones, start=1):
        vol = volumen_agua(area, p)
        esc = escorrentia(vol, coeficiente)

        riesgo = riesgo_hidrico(p)
        print(f"Día {i}: {p} mm → Volumen: {round(vol,2)} m³, Escorrentía: {round(esc,2)} m³ → Riesgo: {riesgo}")