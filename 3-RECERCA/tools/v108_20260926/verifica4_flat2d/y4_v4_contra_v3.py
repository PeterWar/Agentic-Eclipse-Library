"""y4 (verificador adversari 4) · LA v4 NO PERD RES DE LA v3? On canvia la v4 respecte de la v3, i quant, a cada producte.
Productes: fusion_starless (ln R/G, ln B/G, ln G), base_G i compost (control, v3, v4). Zones:
  · P = petjades de la v4 (canvi v4 − v3 a qualsevol dels tres apilats, |G3| > 5·10⁻⁵), dilatades 150 px (els filtres escampen);
  · fora de P, per anells de R☉ (1,02–1,5, 1,5–2,5, 2,5–4, 4–6, 6–10, 10–30);
  · el limbe (0–3, 3–10, 10–30 px de la Lluna), on hi ha les perles i la franja.
Per zona: rms i p99 de |Δ ln (v4/v3)| (ppm), i la mateixa xifra de |Δ ln (v3/control)| com a escala («quant es mou la v4 respecte del que ja
movia la v3»). Si la v4 no perd res, fora de P el canvi v4 − v3 ha de ser ≪ el de la v3.
Color a les petjades: rms Δ ln R/G i Δ ln B/G (v4 − v3) contra Δ ln G (v4 − v3), a P: el que hi posa la v4, és neutre?
Sortida: 4-RESULTATS/v108_20260926/verifica4_flat2d/Y4_V4_CONTRA_V3.json (només lectura; ~10 GB)."""
import json, time
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica4_flat2d'; CAD = A / '4-RESULTATS/v108_20260926/cadena'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
CR = A / '4-RESULTATS/v97_refundacio_20260924'; F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'; F4 = A / '4-RESULTATS/v108_20260926/flat2d_v4'
AP3 = dict(V=F3 / 'apilats/vixen_total.npy', A=F3 / 'apilats/sony_A_total.npy', B=F3 / 'apilats/cau/sony_B_total_v42.npy')
AP4 = dict(V=F4 / 'apilats/vixen_total.npy', A=F4 / 'apilats/sony_A_total.npy', B=F4 / 'apilats/cau/sony_B_total_v42.npy')
t0 = time.time()
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL; del yy, xx
P = np.zeros((H, W), bool)
for k in ('A', 'B', 'V'):
    a = np.asarray(np.load(AP3[k], mmap_mode='r')[..., 1], np.float32); b = np.asarray(np.load(AP4[k], mmap_mode='r')[..., 1], np.float32); ok = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
    d = np.where(ok, np.log(np.maximum(b, 1e-20)) - np.log(np.maximum(a, 1e-20)), 0).astype(np.float32); P |= np.abs(cv2.GaussianBlur(d, (0, 0), 3)) > 5e-5; del a, b, d, ok
P0 = P.copy(); P = cv2.dilate(P.astype(np.uint8), np.ones((301, 301), np.uint8)) > 0
print('P', round(float(P0.mean()) * 100, 3), '% del llenç; dilatada', round(float(P.mean()) * 100, 2), '%', f'{time.time()-t0:.0f}s', flush=True)
ZONES = {'P_petjades': P & (DL > 30)}
for r0, r1 in ((1.02, 1.5), (1.5, 2.5), (2.5, 4), (4, 6), (6, 10), (10, 30)): ZONES[f'fora_P_R{r0}-{r1}'] = ~P & (RS >= r0) & (RS < r1) & (DL > 30)
for d0, d1 in ((0, 3), (3, 10), (10, 30)): ZONES[f'limbe_{d0}-{d1}px'] = (DL >= d0) & (DL < d1)
def estad(d, ok):
    o = {}
    for z, m in ZONES.items():
        k = m & ok
        if k.sum() < 100: continue
        x = np.abs(d[k]); o[z] = dict(n=int(k.sum()), rms_ppm=round(1e6 * float(np.sqrt((x.astype(np.float64) ** 2).mean())), 2), p99_ppm=round(1e6 * float(np.percentile(x, 99)), 2),
                                      max_ppm=round(1e6 * float(x.max()), 1), n_mes_1pc=int((x > 0.01).sum()))
    return o
R = {'petjades_pc_llenc': round(float(P0.mean()) * 100, 3)}
def carrega(p, f=None):
    x = np.load(p, mmap_mode='r'); x = np.asarray(x if f is None else f(x), np.float32); return x
PRODS = {'base_G': {v: CAD / d / 'lineal/base_G.npy' for v, d in (('control', 'control'), ('v3', 'flat2d_v3'), ('v4', 'flat2d_v4'))},
         'compost': {'control': F2 / 'compost_control.npy', 'v3': F3 / 'compost_flat2d_v3.npy', 'v4': F4 / 'compost_flat2d_v4.npy'}}
for nom, ps in PRODS.items():
    X = {v: carrega(p) for v, p in ps.items()}; ok = np.ones((H, W), bool)
    for v in X: ok &= np.isfinite(X[v]) & (X[v] > 0)
    L = {v: np.where(ok, np.log(np.maximum(X[v], 1e-20)), 0).astype(np.float32) for v in X}; del X
    R[nom] = dict(v4_menys_v3=estad(L['v4'] - L['v3'], ok), v3_menys_control=estad(L['v3'] - L['control'], ok))
    print(nom, json.dumps(R[nom]['v4_menys_v3']), f'{time.time()-t0:.0f}s', flush=True); del L
# fusion_starless: ln R/G, ln B/G, ln G
F = {v: np.load(CAD / d / 'lineal/fusion_starless.npy', mmap_mode='r') for v, d in (('control', 'control'), ('v3', 'flat2d_v3'), ('v4', 'flat2d_v4'))}
ok = np.ones((H, W), bool); LG = {}
for v in F:
    g = np.asarray(F[v][..., 1], np.float32); ok &= np.isfinite(g) & (g > 0); LG[v] = np.log(np.maximum(g, 1e-20)).astype(np.float32); del g
for c, nomc in ((None, 'lnG'), (0, 'lnRG'), (2, 'lnBG')):
    if c is None: L = LG
    else:
        L = {}; okc = ok.copy()
        for v in F:
            x = np.asarray(F[v][..., c], np.float32); okc &= np.isfinite(x) & (x > 0); L[v] = (np.log(np.maximum(x, 1e-20)) - LG[v]).astype(np.float32); del x
    k = ok if c is None else okc
    R.setdefault('fusion_starless', {})[nomc] = dict(v4_menys_v3=estad(np.where(k, L['v4'] - L['v3'], 0), k), v3_menys_control=estad(np.where(k, L['v3'] - L['control'], 0), k))
    # suavitzat σ20 (el color que es veu): rms dins P
    d20 = cv2.GaussianBlur(np.where(k, L['v4'] - L['v3'], 0).astype(np.float32), (0, 0), 20); kk = P & k & (DL > 30)
    R['fusion_starless'][nomc]['v4_menys_v3_sigma20_dins_P_rms_ppm'] = round(1e6 * float(np.sqrt((d20[kk].astype(np.float64) ** 2).mean())), 3)
    R['fusion_starless'][nomc]['v4_menys_v3_sigma20_dins_P_max_ppm'] = round(1e6 * float(np.abs(d20[kk]).max()), 2)
    print('fusion', nomc, json.dumps(R['fusion_starless'][nomc]['v4_menys_v3'].get('P_petjades')), R['fusion_starless'][nomc]['v4_menys_v3_sigma20_dins_P_rms_ppm'], f'{time.time()-t0:.0f}s', flush=True)
    if c is not None: del L
    (OUT / 'Y4_V4_CONTRA_V3.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
(OUT / 'Y4_V4_CONTRA_V3.json').write_text(json.dumps(R, ensure_ascii=False, indent=1)); print('FET', f'{time.time()-t0:.0f}s')
