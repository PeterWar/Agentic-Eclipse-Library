"""x5 (verificador adversari, 27-09) · La vora de la dada (diagonal de baix a la dreta, dins del marc) i el canvi a escala mitjana (σ8 − σ64)
de ln V108 − ln V107 al llenç sencer, per buscar línies, anells, costures o discos que el gra fi amaga. Sortida: vistes/X5_*.png i text."""
from pathlib import Path
import numpy as np, cv2
R0 = Path('/Users/USUARI/Desktop/Eclipse 2026'); OUT = R0 / '4-RESULTATS/v108_20260926/verifica_v108_final'; CO = OUT / 'composts'; VI = OUT / 'vistes'
W, H = 10551, 7506; MARC = (1325, 1142, 9348, 6263)
L7 = np.load(CO / 'L_V107.npy', mmap_mode='r'); L8 = np.load(CO / 'L_V108.npy', mmap_mode='r')
def div(v, s):
    v = np.clip(v / s, -1, 1); return (np.stack([np.clip(1 - np.maximum(v, 0), 0, 1), 1 - np.abs(v), np.clip(1 + np.minimum(v, 0), 0, 1)], -1) * 255).astype(np.uint8)
# 1) retall de la vora diagonal dins del marc
cx, cy, h = 8434, 6083, 400
a7 = np.asarray(L7[cy - h:cy + h, cx - h:cx + h], np.float32); a8 = np.asarray(L8[cy - h:cy + h, cx - h:cx + h], np.float32)
l7, l8 = np.log(np.maximum(a7, 1e-4)), np.log(np.maximum(a8, 1e-4)); ok = (a7 > 2e-3)
lo, hi = np.percentile(l7[ok], [1, 99.5]); g = lambda l: cv2.cvtColor((np.clip((l - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
cv2.imwrite(str(VI / 'X5_VORA_V107_V108_CANVI.png'), np.concatenate([g(l7), g(l8), div(np.where(ok, l8 - l7, 0), 0.10)], 1))
# perfil perpendicular a la vora: el quocient per distància a la vora de dada (alfa efectiva > 0 de L)
dada = (np.asarray(L7, np.float32) > 1e-3)
dist = cv2.distanceTransform(dada.astype(np.uint8), cv2.DIST_L2, 5)
mc = np.zeros((H, W), bool); mc[MARC[1]:MARC[3], MARC[0]:MARC[2]] = True
rat = np.log(np.maximum(np.asarray(L8, np.float32), 1e-4)) - np.log(np.maximum(np.asarray(L7, np.float32), 1e-4))
print('ln V108/V107 per distància a la vora de la dada (dins del marc): mediana i p5/p95')
for a, b in ((0, 2), (2, 5), (5, 10), (10, 20), (20, 40), (40, 80), (80, 150), (150, 300), (300, 600)):
    m = mc & dada & (dist >= a) & (dist < b)
    if m.sum(): x = rat[m]; print(f'  {a:>3}-{b:<3} px: n={m.sum():>8}  med={100*np.median(x):+.2f} %  p5={100*np.percentile(x,5):+.2f}  p95={100*np.percentile(x,95):+.2f}')
del dist, dada
# 2) canvi a escala mitjana, llenç sencer (pas 3)
S = 3; r = cv2.resize(rat, (W // S, H // S), interpolation=cv2.INTER_AREA); del rat
bp = cv2.GaussianBlur(r, (0, 0), 8 / S) - cv2.GaussianBlur(r, (0, 0), 64 / S)
cv2.imwrite(str(VI / 'X5_CANVI_ESCALA_MITJANA_8-64.png'), div(bp, 0.03))
cv2.imwrite(str(VI / 'X5_CANVI_GRAN_ESCALA_s32.png'), div(cv2.GaussianBlur(r, (0, 0), 32 / S), 0.25))
# 3) (afegit) la vora de dada a cada versió: L a 0–20 px de la vora relativa a 40–80 px, dins del marc (rivet brillant?)
L7a = np.asarray(L7, np.float32); L8a = np.asarray(L8, np.float32); dada = L7a > 1e-3
dist = cv2.distanceTransform(dada.astype(np.uint8), cv2.DIST_L2, 5); del dada
for nom, A in (('V107', L7a), ('V108', L8a)):
    ref = np.median(A[mc & (dist >= 40) & (dist < 80)])
    print(nom, 'vora/40–80 px:', ' '.join(f'{a}-{b}px: med {np.median(A[mc & (dist >= a) & (dist < b)]) / ref:.3f} p95 {np.percentile(A[mc & (dist >= a) & (dist < b)], 95) / ref:.3f}' for a, b in ((0, 3), (3, 10), (10, 20), (20, 40))))
