"""w9 (verificador adversari 2) · (a) Les taques de pols del canvi a l'apilat Sony A (vista W5_6): cura o injecció? Els màxims locals |Δ| del
canvi (σ10 − σ60) dins de la zona de les taques (x 5.400–8.200, y 800–3.300), amb la mateixa prova que w8 (E_abans contra Δ, nul a l'atzar).
(b) Color: ln(R/G) i ln(B/G) de fusion_starless, banda σ20 − σ200; s = (ΣY² − ΣX²)/ΣΔ² (−1 cura, +1 injecció) i s_nul (X desplaçat), per anells.
Sortida: W9_POLS_SONY_I_COLOR.json"""
import json
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica2_marrons'
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; CAD = A / '4-RESULTATS/v108_20260926/cadena'; CR = A / '4-RESULTATS/v97_refundacio_20260924'
W, H = 10551, 7506; SOL = np.array([5361.768, 3775.748]); RSOL = 440.603
def lnm(x):
    m = (np.isfinite(x) & (x > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(x, 1e-12)), 0).astype(np.float32), m
def ng(l, m, s): return cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
R = {}
a = np.load(CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', mmap_mode='r'); b = np.load(F2 / 'apilats/sony_A_total.npy', mmap_mode='r')
va, ma = lnm(np.asarray(a[..., 1], np.float32)); vb, mb = lnm(np.asarray(b[..., 1], np.float32)); m = ma * mb
d = np.where(m > 0, vb - va, 0).astype(np.float32); dd = ng(d, m, 10) - ng(d, m, 60)
zona = np.zeros((H, W), bool); zona[800:3300, 5400:8200] = True; ok = (cv2.erode(m, np.ones((251, 251), np.uint8)) > 0)
mx = cv2.dilate(np.abs(dd), np.ones((121, 121), np.uint8)); pk = ok & zona & (np.abs(dd) == mx) & (np.abs(dd) > 0.0008)
ys, xs = np.nonzero(pk)
yy, xx = np.mgrid[-120:121, -120:121]; rr = np.hypot(yy, xx); DISC = rr < 30; ANELL = (rr >= 60) & (rr < 100)
def E(l, x, y):
    t = l[y - 120:y + 121, x - 120:x + 121]; k = m[y - 120:y + 121, x - 120:x + 121] > 0
    if t.shape != rr.shape or (k & DISC).sum() < 0.9 * DISC.sum(): return np.nan
    return float(1e4 * (t[k & DISC].mean() - t[k & ANELL].mean()))
rng = np.random.default_rng(11); taques = []
for y, x in zip(ys, xs):
    r0 = np.hypot(x - SOL[0], y - SOL[1]); nul = []
    while len(nul) < 60:
        ang = rng.uniform(0, 2 * np.pi); r_ = r0 * rng.uniform(0.9, 1.1); cx, cy = int(SOL[0] + r_ * np.cos(ang)), int(SOL[1] + r_ * np.sin(ang))
        if 130 < cx < W - 130 and 130 < cy < H - 130 and ok[cy, cx]:
            v = E(va, cx, cy)
            if np.isfinite(v): nul.append(v)
    nul = np.array(nul); ea, eb = E(va, x, y), E(vb, x, y)
    taques.append(dict(x=int(x), y=int(y), R_sol=round(float(r0 / RSOL), 2), dd_pc=round(100 * float(dd[y, x]), 3), E_abans=round(ea, 1), E_despres=round(eb, 1), canvi=round(eb - ea, 1),
                       fraccio_curada=round(-ea / (eb - ea), 2) if abs(eb - ea) > 1 else None, sd_nul=round(float(nul.std()), 1), z_abans=round(float((ea - nul.mean()) / nul.std()), 2), z_despres=round(float((eb - nul.mean()) / nul.std()), 2)))
tq = [t for t in taques if np.isfinite(t['canvi'])]
num = sum(-t['E_abans'] * t['canvi'] for t in tq); den = sum(t['canvi'] ** 2 for t in tq)
R['sonyA_taques'] = dict(n=len(tq), fraccio_curada_global=round(num / den, 3), llista=sorted(tq, key=lambda t: -abs(t['canvi']))[:15]); print('SONY A', R['sonyA_taques']['n'], R['sonyA_taques']['fraccio_curada_global'], flush=True)
for t in R['sonyA_taques']['llista']: print(t, flush=True)
del va, vb, ma, mb, m, d, dd, mx
# ---- color
a = np.load(CAD / 'control/lineal/fusion_starless.npy', mmap_mode='r'); b = np.load(CAD / 'flat2d_v2/lineal/fusion_starless.npy', mmap_mode='r')
yy, xx = np.mgrid[0:H, 0:W]; RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; del yy, xx
Ga = np.asarray(a[..., 1], np.float32); Gb = np.asarray(b[..., 1], np.float32)
for nm, c in (('R_G', 0), ('B_G', 2)):
    la, m1 = lnm(np.asarray(a[..., c], np.float32) / np.maximum(Ga, 1e-12)); lb, m2 = lnm(np.asarray(b[..., c], np.float32) / np.maximum(Gb, 1e-12)); m = m1 * m2 * (Ga > 0)
    X = ng(la, m, 20) - ng(la, m, 200); Y = ng(lb, m, 20) - ng(lb, m, 200); D = Y - X; Xs = np.roll(np.roll(X, 97, 1), -71, 0)
    okc = cv2.erode(m, np.ones((401, 401), np.uint8)) > 0; oks = okc & np.roll(np.roll(okc, 97, 1), -71, 0); o = {}
    for r0, r1 in ((1.5, 3), (3, 6), (6, 10), (10, 30)):
        k = okc & (RS >= r0) & (RS < r1); ks = oks & (RS >= r0) & (RS < r1)
        EX = float((X[k].astype(np.float64) ** 2).sum()); EY = float((Y[k].astype(np.float64) ** 2).sum()); ED = float((D[k].astype(np.float64) ** 2).sum())
        EDs = float((D[ks].astype(np.float64) ** 2).sum()); EXs = float((Xs[ks].astype(np.float64) ** 2).sum()); EYs = float(((Xs[ks] + D[ks]).astype(np.float64) ** 2).sum())
        o[f'{r0}-{r1}'] = dict(s=round((EY - EX) / ED, 3), s_nul=round((EYs - EXs) / EDs, 3), dE_pc=round(100 * (EY / EX - 1), 2), rms_D_ppm=round(1e4 * np.sqrt(ED / k.sum()), 2), rms_X_ppm=round(1e4 * np.sqrt(EX / k.sum()), 2))
    R[f'color_{nm}'] = o; print(nm, o, flush=True); del la, lb, X, Y, D, Xs
(OUT / 'W9_POLS_SONY_I_COLOR.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
