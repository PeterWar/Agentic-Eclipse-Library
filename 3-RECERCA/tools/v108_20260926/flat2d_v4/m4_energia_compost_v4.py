"""m4_energia_compost_v4 (V108, flat2d_v4) · CÒPIA del x1 del verificador 3 (x1_energia_compost.py) amb la v3 i la v4 (en lloc de la v2 i la v3):
l'energia de textura del compost (o de la base) per bandes i anells de R☉, v/control, i els mapes per rajoles de 256 px del llenç sencer.
És el que el verificador 3 va trobar que l'INFORME de la v3 no declarava (σ4–40 −23 / −18 / −14 % a 4–6 / 6–10 / 10–30 R☉).
Sortida: 4-RESULTATS/v108_20260926/flat2d_v4/M4_ENERGIA_<qui>.json i M4_MAPA_<qui>_*.png
─── Text del verificador ───
x1 (verificador adversari 3) · On canvia l'ENERGIA de textura del compost (i de la base)? Mapa per rajoles de 256 px del llenç sencer.
Per a control, v2 i v3: banda del ln (σa − σb), energia mitjana per rajola; mapa log2(E_v/E_control) i resum per anells de R☉.
Motiu: a la VISTA_7 de la v3 (σ4−σ40) hi ha zones clarament més pàl·lides a esquerra i dreta del Sol; cal saber si és cura (patró fix tret)
o pèrdua de detall, i si la v2 ja ho feia.
Ús: x1_energia_compost.py [compost|base]   Sortida: 4-RESULTATS/v108_20260926/verifica3_flat2d/X1_ENERGIA_<qui>.json i X1_MAPA_<qui>_*.png"""
import json, sys
from pathlib import Path
import numpy as np, cv2
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/flat2d_v4'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'; F4 = A / '4-RESULTATS/v108_20260926/flat2d_v4'; CAD = A / '4-RESULTATS/v108_20260926/cadena'
qui = (sys.argv[1:] or ['compost'])[0]
P = {'compost': {'control': F2 / 'compost_control.npy', 'v3': F3 / 'compost_flat2d_v3.npy', 'v4': F4 / 'compost_flat2d_v4.npy'},
     'base': {'control': CAD / 'control/lineal/base_G.npy', 'v3': CAD / 'flat2d_v3/lineal/base_G.npy', 'v4': CAD / 'flat2d_v4/lineal/base_G.npy'}}[qui]
BANDES = [(0, 1), (1, 4), (4, 40), (40, 200)]
T = 256; ny, nx = H // T, W // T
yy, xx = np.mgrid[0:ny, 0:nx]; RS = np.hypot((xx + .5) * T - SOL[0], (yy + .5) * T - SOL[1]) / RSOL
ANELLS = [(1.05, 1.5), (1.5, 2.5), (2.5, 4), (4, 6), (6, 10), (10, 30)]
def carrega(p):
    x = np.asarray(np.load(p, mmap_mode='r'), np.float32); m = ((x > 0) & np.isfinite(x)).astype(np.float32)
    return np.where(m > 0, np.log(np.maximum(x, 1e-12)), 0).astype(np.float32), m
L = {}; M = None
for v, p in P.items():
    L[v], m = carrega(p); M = m if M is None else M * m
ok = cv2.erode(M, np.ones((81, 81), np.uint8)) > 0
dl = np.hypot(*np.meshgrid(np.arange(W) - 5375.787, np.arange(H) - 3775.977)) - 452.98; ok &= dl > 12; del dl
def tiles(e):
    e = np.where(ok, e, 0).astype(np.float64)[:ny * T, :nx * T].reshape(ny, T, nx, T).sum((1, 3)); n = ok[:ny * T, :nx * T].reshape(ny, T, nx, T).sum((1, 3))
    return e, n
R = {}
for a, b in BANDES:
    E = {}
    for v in P:
        l = L[v]; g = lambda s: (l if s == 0 else cv2.GaussianBlur(l * M, (0, 0), s) / np.maximum(cv2.GaussianBlur(M, (0, 0), s), 1e-6))
        d = (g(a) - g(b)).astype(np.float32); E[v], n = tiles(d * d); del d
    val = n > 0.8 * T * T; res = {}
    for r0, r1 in ANELLS:
        k = val & (RS >= r0) & (RS < r1)
        if k.sum() < 4: continue
        rr = {v: float(E[v][k].sum() / E['control'][k].sum() - 1) for v in ('v3', 'v4')}
        q3 = np.log2(E['v3'][k] / E['control'][k]); q4 = np.log2(E['v4'][k] / E['control'][k])
        res[f'{r0}-{r1}'] = dict(dE_v3_pc=round(100 * rr['v3'], 2), dE_v4_pc=round(100 * rr['v4'], 2), rajoles=int(k.sum()),
                                 v3_rajoles_p5_p95_pc=[round(100 * (2 ** float(np.percentile(q3, 5)) - 1), 1), round(100 * (2 ** float(np.percentile(q3, 95)) - 1), 1)],
                                 v4_rajoles_p5_p95_pc=[round(100 * (2 ** float(np.percentile(q4, 5)) - 1), 1), round(100 * (2 ** float(np.percentile(q4, 95)) - 1), 1)])
    R[f'{a}-{b}px'] = res; print(qui, a, b, json.dumps(res), flush=True)
    fig, ax = plt.subplots(1, 2, figsize=(22, 8.5))
    for i, v in enumerate(('v4', 'v3')):
        q = np.where(val, 100 * (E[v] / np.maximum(E['control'], 1e-30) - 1), np.nan); cm = plt.get_cmap('bwr').copy(); cm.set_bad('0.85')
        im = ax[i].imshow(q, cmap=cm, vmin=-20, vmax=20); ax[i].set_title(f'{qui} · energia banda σ{a}–σ{b}: {v}/control − 1 (%) · rajoles de {T} px'); ax[i].axis('off')
        ax[i].plot(SOL[0] / T - .5, SOL[1] / T - .5, 'k+')
    fig.colorbar(im, ax=ax, fraction=0.02); fig.savefig(OUT / f'M4_MAPA_{qui}_s{a}_{b}.png', dpi=80); plt.close(fig)
(OUT / f'M4_ENERGIA_{qui}.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
