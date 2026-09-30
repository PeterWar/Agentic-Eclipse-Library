"""w6 (verificador adversari 2) · Els dos píxels de la protuberància de l'esquerra (180°, 17,8 px del limbe) que surten del domini de la franja.
Retall 81×81 al voltant de (4901, 3782) de: base lineal (base_G), capa 3 (L3_RGB, mitjana), NRGF 41, RHEF 45, ACHF 47, MGN 54, WOW 56 i compost,
abans (control = V107) i després (flat2d_v2). Imprimeix els 3×3 centrals i compta quants píxels del retall canvien > 1 %, > 10 %.
Sortida: W6_PROTUBERANCIA.json i W6_PROTUBERANCIA.png"""
import json
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica2_marrons'
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; CAD = A / '4-RESULTATS/v108_20260926/cadena'
X0, Y0, M = 4901, 3782, 40; sl = (slice(Y0 - M, Y0 + M + 1), slice(X0 - M, X0 + M + 1))
def tall(p, rgb=False):
    a = np.load(p, mmap_mode='r'); x = np.asarray(a[sl], np.float64); return x.mean(-1) if rgb else x
CAPES = {'base_G (lineal)': ('lineal/base_G.npy', False), 'L3 base (RGB)': ('estat_v108/L3_RGB.npy', True), 'L41 NRGF': ('estat_v108/L41_G.npy', False),
         'L45 RHEF': ('estat_v108/L45_G.npy', False), 'L47 ACHF': ('estat_v108/L47_G.npy', False), 'L54 MGN': ('estat_v108/L54_G.npy', False), 'L56 WOW': ('estat_v108/L56_G.npy', False)}
R = {}; fig, ax = plt.subplots(3, len(CAPES) + 1, figsize=(4 * (len(CAPES) + 1), 12))
items = list(CAPES.items()) + [('compost', None)]
for j, (nom, v) in enumerate(items):
    if v is None: a, b = tall(F2 / 'compost_control.npy'), tall(F2 / 'compost_flat2d_v2.npy')
    else: a, b = tall(CAD / 'control' / v[0], v[1]), tall(CAD / 'flat2d_v2' / v[0], v[1])
    with np.errstate(all='ignore'): r = b / a - 1
    c = (slice(M - 2, M + 3), slice(M - 2, M + 3))
    R[nom] = dict(abans_5x5=np.round(a[c], 1).tolist(), despres_5x5=np.round(b[c], 1).tolist(), n_px_canvi_gt_1pc=int(np.nansum(np.abs(r) > 0.01)), n_px_canvi_gt_10pc=int(np.nansum(np.abs(r) > 0.10)),
                  max_rel=float(np.nanmax(np.abs(r[np.isfinite(r)]))) if np.isfinite(r).any() else None)
    vmin, vmax = np.nanpercentile(a, [1, 99.5])
    ax[0, j].imshow(a, cmap='gray', vmin=vmin, vmax=vmax); ax[0, j].set_title(f'{nom} · abans'); ax[1, j].imshow(b, cmap='gray', vmin=vmin, vmax=vmax); ax[1, j].set_title('després (mateixa escala)')
    ax[2, j].imshow(np.clip(np.nan_to_num(r), -0.2, 0.2), cmap='bwr', vmin=-0.2, vmax=0.2); ax[2, j].set_title('després/abans − 1 (±20 %)')
    for k in range(3): ax[k, j].axis('off')
    print(nom, R[nom]['n_px_canvi_gt_1pc'], R[nom]['n_px_canvi_gt_10pc'], 'centre abans/després', R[nom]['abans_5x5'][2][2], R[nom]['despres_5x5'][2][2], flush=True)
plt.tight_layout(); plt.savefig(OUT / 'W6_PROTUBERANCIA.png', dpi=70)
(OUT / 'W6_PROTUBERANCIA.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
