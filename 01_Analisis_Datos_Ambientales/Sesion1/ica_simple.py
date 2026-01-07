import numpy as np
# Datos simulados de laboratorio
dbo = np.array([6.2, 7.1, 5.8, 6.5, 7.0])        # mg/L
sst = np.array([35, 40, 32, 38, 45])             # mg/L
ph = np.array([7.1, 7.0, 7.2, 6.9, 7.3])         # unidades
# Un "ICA" básico hecho para practicar (no real)
score_dbo = 100 - (np.mean(dbo) * 5)
score_sst = 100 - (np.mean(sst) * 0.8)
score_ph = 100 - abs(7 - np.mean(ph)) * 20
ICA = (score_dbo + score_sst + score_ph) / 3

print("ICA aproximado:", ICA)