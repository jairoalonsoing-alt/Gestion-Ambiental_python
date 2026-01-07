import numpy as np
# Caudales diarios (m³/s) de un río en una semana
caudales = np.array([1.8, 2.1, 2.5, 2.0, 1.9, 2.3, 2.4])
promedio = np.mean(caudales)
maximo = np.max(caudales)
minimo = np.min(caudales)
print("Caudales:", caudales)
print("Promedio:", promedio, "m³/s")
print("Máximo:", maximo, "m³/s")
print("Mínimo:", minimo, "m³/s")