"""y7 (verificador adversari 4) · VISTA DEL LLENÇ SENCER: el canvi v4 − v3 del compost (ln, σ3, ±2 %) amb cada petjada de l'Y1 marcada segons la prova s
amb el cel anul·lat a σ4–40 (verd: cura, s ≤ −0,5; taronja: passa de llarg, −0,5 < s ≤ 0,5; vermell: com el nul, s > 0,5). Cercle gruixut = Vixen.
Sortida: 4-RESULTATS/v108_20260926/verifica4_flat2d/Y7_VISTA_compost_v4_menys_v3_petjades.png (a 1/4)."""
import json
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica4_flat2d'
F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'; F4 = A / '4-RESULTATS/v108_20260926/flat2d_v4'
a = np.asarray(np.load(F3 / 'compost_flat2d_v3.npy', mmap_mode='r'), np.float32); b = np.asarray(np.load(F4 / 'compost_flat2d_v4.npy', mmap_mode='r'), np.float32)
ok = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0); d = np.where(ok, np.log(np.maximum(b, 1e-12) / np.maximum(a, 1e-12)), 0).astype(np.float32); del a, b
d = cv2.GaussianBlur(d, (0, 0), 3); t = np.clip(d / 0.02, -1, 1)
img = np.full(d.shape + (3,), 255, np.uint8)
img[..., 2] = np.where(t > 0, 255, 255 * (1 + t)).astype(np.uint8); img[..., 1] = (255 * (1 - np.abs(t))).astype(np.uint8); img[..., 0] = np.where(t < 0, 255, 255 * (1 - t)).astype(np.uint8)
img[~ok] = 215
R = json.loads((OUT / 'Y1_CURA_PETJADES.json').read_text())
for tren in ('sony_A', 'sony_B', 'vixen'):
    for p in R[tren]['petjades']['banda_4_40']:
        s = p['s']; col = (0, 170, 0) if s <= -0.5 else ((0, 140, 255) if s <= 0.5 else (0, 0, 230))
        r = int(max(60, np.sqrt(p['area']) * 0.9)); cv2.circle(img, tuple(p['centre']), r, col, 18 if tren == 'vixen' else 8)
sm = cv2.resize(img, (img.shape[1] // 4, img.shape[0] // 4), interpolation=cv2.INTER_AREA)
cap = np.full((60, sm.shape[1], 3), 255, np.uint8)
cv2.putText(cap, 'compost ln(v4/v3) sigma3 +-2 % (vermell = mes clar a la v4) - petjades per la prova s al cel anullat, sigma4-40: verd cura, taronja passa de llarg, vermell com el nul; gruixut = Vixen',
            (10, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 1, cv2.LINE_AA)
cv2.imwrite(str(OUT / 'Y7_VISTA_compost_v4_menys_v3_petjades.png'), np.vstack([cap, sm])); print('FET')
