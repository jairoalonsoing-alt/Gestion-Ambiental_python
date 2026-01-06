import numpy as np
# Crear un arreglo de datos (ejemplo: concentraciones de sólidos mg/L)
datos = np.array([12.5, 15.2, 14.8, 13.1, 16.0, 15.8])
# Calcular promedio, máximo y mínimo
promedio = np.mean(datos)
maximo = np.max(datos)
minimo = np.min(datos)

print("Datos:", datos)
print("Promedio:", promedio)
print("Máximo:", maximo)
print("Mínimo:", minimo)
