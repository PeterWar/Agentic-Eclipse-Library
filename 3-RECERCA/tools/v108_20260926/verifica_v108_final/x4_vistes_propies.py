"""x4 (verificador adversari de la V108 final, 27-09) · Vistes pròpies del llenç sencer (pas 3) a partir dels composts de x2 (llegits dels PSB):
  X4_V108_PLE_estirada.png          : ln L de la V108, estirat per percentils (la imatge sencera)
  X4_V107_V108_estirada_costat.png  : V107 | V108 amb el MATEIX estirament (el de la V107)
  X4_PASALT_CANVI.png               : pas alt (σ2 − σ25) de ln V108 − ln V107, ±1 %: línies, anells, costures, discos, taques del canvi
  X4_PASALT_V108.png                : pas alt (σ2 − σ25) de ln V108, ±6 %: el detall tal com queda
  X4_COLOR_CANVI.png                : Δ ln R/G i Δ ln B/G (σ8) de la V108 contra la V107, ±1 %, dels PSB (compost PLE en RGB a pas 3)
Sortida: 4-RESULTATS/v108_20260926/verifica_v108_final/vistes/."""
import sys, time
from pathlib import Path
import numpy as np, cv2
R0 = Path('/Users/USUARI/Desktop/Eclipse 2026')
OUT = R0 / '4-RESULTATS/v108_20260926/verifica_v108_final'; CO = OUT / 'composts'; VI = OUT / 'vistes'
W, H = 10551, 7506; S = 3; T0 = time.time()
L = {p: np.load(CO / f'L_{p}.npy', mmap_mode='r') for p in ('V107', 'V108')}
def red(a): return cv2.resize(np.ascontiguousarray(a, np.float32), (W // S, H // S), interpolation=cv2.INTER_AREA)
l7 = np.log(np.maximum(red(L['V107']), 1e-4)); l8 = np.log(np.maximum(red(L['V108']), 1e-4))
lo, hi = np.percentile(l7[l7 > np.log(2e-4)], [0.5, 99.8])
g = lambda l: (np.clip((l - lo) / (hi - lo), 0, 1) ** 0.9 * 255).astype(np.uint8)
cv2.imwrite(str(VI / 'X4_V108_PLE_estirada.png'), g(l8))
cv2.imwrite(str(VI / 'X4_V107_V108_estirada_costat.png'), np.concatenate([g(l7), np.full((l7.shape[0], 20), 255, np.uint8), g(l8)], 1))
def div(v, s):
    v = np.clip(v / s, -1, 1); return (np.stack([np.clip(1 - np.maximum(v, 0), 0, 1), 1 - np.abs(v), np.clip(1 + np.minimum(v, 0), 0, 1)], -1) * 255).astype(np.uint8)  # BGR: vermell +, blau −
d = l8 - l7; hp = cv2.GaussianBlur(d, (0, 0), 0.7) - cv2.GaussianBlur(d, (0, 0), 25 / S)
cv2.imwrite(str(VI / 'X4_PASALT_CANVI.png'), div(hp, 0.01))
hp8 = cv2.GaussianBlur(l8, (0, 0), 0.7) - cv2.GaussianBlur(l8, (0, 0), 25 / S)
cv2.imwrite(str(VI / 'X4_PASALT_V108.png'), ((np.clip(hp8 / 0.06, -1, 1) + 1) * 127.5).astype(np.uint8))
# color: recompon el PLE en RGB a pas 3 no cal; fem servir C1? No: el color es mira al compost PLE de v108_final (RGB2, pas 2) validat per x2 via L
VF = R0 / '4-RESULTATS/v108_20260926/v108_final/composts'
R7 = np.load(VF / 'RGB2_V107.npy', mmap_mode='r'); R8 = np.load(VF / 'RGB2_V108.npy', mmap_mode='r')
def lr(a, i, j): return np.log(np.maximum(np.asarray(a[..., i], np.float32), 1e-4)) - np.log(np.maximum(np.asarray(a[..., j], np.float32), 1e-4))
drg = cv2.GaussianBlur(lr(R8, 0, 1) - lr(R7, 0, 1), (0, 0), 4); dbg = cv2.GaussianBlur(lr(R8, 2, 1) - lr(R7, 2, 1), (0, 0), 4)
k = drg.shape[1]
cv2.imwrite(str(VI / 'X4_COLOR_CANVI.png'), np.concatenate([div(drg, 0.01), np.full((drg.shape[0], 20, 3), 255, np.uint8), div(dbg, 0.01)], 1)[::2, ::2])
print('Δ ln R/G σ4: p99 |.| =', float(np.percentile(np.abs(drg), 99)), 'max', float(np.abs(drg).max()), '· Δ ln B/G: p99', float(np.percentile(np.abs(dbg), 99)), 'max', float(np.abs(dbg).max()))
print('FET', round(time.time() - T0), 's')
