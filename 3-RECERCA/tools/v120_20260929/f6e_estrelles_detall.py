"""f6e (V120, 29-09-2026) · DETALL DE LA PORTA D'ESTRELLES del f6: el residu Vixen − Sony deformada estrella a estrella, amb el S/N de cada
centroide, la posició (r, angle) i el residu que el camp ja corregia; per saber si el rms d'A (1,49 px > 1 px) és un patró del camp o una o dues
estrelles de S/N baix. Mateixa mesura que el f6 (centroide subpíxel, S/N ≥ 6 a totes dues). Ús: f6e_estrelles_detall.py <carpeta_sony_v> <carpeta_sortida>"""

import sys, json, time, importlib.util, numpy as np, cv2
from pathlib import Path
from scipy import ndimage as ndi
SV, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
sys.argv = [sys.argv[0], str(OUT / '_b1')]
R = Path(__file__).resolve().parents[3]; t0 = time.time()
spec = importlib.util.spec_from_file_location('b1', R / '3-RECERCA/tools/v117_20260929/b1_filtre_coherent_AB.py'); b1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b1)
spec = importlib.util.spec_from_file_location('camp_v120', Path(__file__).with_name('camp_v120.py')); f4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(f4)   # el camp definitiu (autosuficient)
H, W, SOL, RS = b1.H, b1.W, b1.SOL, b1.RS
def log(*a): print(f'[{time.time() - t0:5.0f}s]', *a, flush=True)
import os; MODEL = json.load(open(SV.parent / 'f1' / os.environ.get('V120_MODEL', 'CAMP_V120.json')))
AP = R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats'; S4 = R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/d4/products/sources'
def lumin(p, fnan=True):
    t = np.load(p, mmap_mode='r'); L = np.zeros((H, W), np.float32)
    for y0 in range(0, H, 1024):
        a = np.asarray(t[y0:y0 + 1024], np.float32); ok = np.all(np.isfinite(a) & (a > 0), 2)
        L[y0:y0 + 1024] = np.where(ok, (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4, np.nan if fnan else 0)
    return L
yy8, xx8 = np.mgrid[-12:13, -12:13].astype(np.float64); rr8 = np.hypot(xx8, yy8); ring = (rr8 >= 8) & (rr8 <= 12); Xr = np.stack([np.ones(ring.sum()), xx8[ring], yy8[ring]], 1)
def centroide(Lmm, x, y):
    xi, yi = int(round(x)), int(round(y))
    if xi < 30 or yi < 30 or xi + 30 >= W or yi + 30 >= H: return None
    big = np.asarray(Lmm[yi - 22:yi + 23, xi - 22:xi + 23], np.float64)
    if not np.isfinite(big).all(): return None
    sm = cv2.GaussianBlur(big, (0, 0), 1.5); yb, xb = np.mgrid[-22:23, -22:23]; sm[np.hypot(xb, yb) > 10] = -np.inf
    j = np.unravel_index(np.argmax(sm), sm.shape); cx, cy = xi + xb[j], yi + yb[j]
    for _ in range(6):
        cxi, cyi = int(round(cx)), int(round(cy)); w = np.asarray(Lmm[cyi - 12:cyi + 13, cxi - 12:cxi + 13], np.float64)
        if w.shape != (25, 25) or not np.isfinite(w).all(): return None
        cf = np.linalg.lstsq(Xr, w[ring], rcond=None)[0]; z = w - (cf[0] + cf[1] * xx8 + cf[2] * yy8)
        dx, dy = xx8 - (cx - cxi), yy8 - (cy - cyi); mk = (np.hypot(dx, dy) <= 4) & (z > 0)
        if z[mk].sum() <= 0: return None
        ncx = cxi + (xx8[mk] * z[mk]).sum() / z[mk].sum(); ncy = cyi + (yy8[mk] * z[mk]).sum() / z[mk].sum(); done = np.hypot(ncx - cx, ncy - cy) < 0.01; cx, cy = ncx, ncy
        if done: break
    cxi, cyi = int(round(cx)), int(round(cy)); w = np.asarray(Lmm[cyi - 12:cyi + 13, cxi - 12:cxi + 13], np.float64); cf = np.linalg.lstsq(Xr, w[ring], rcond=None)[0]
    z = w - (cf[0] + cf[1] * xx8 + cf[2] * yy8); rs_ = w[ring] - Xr @ cf; sd = 1.4826 * np.median(np.abs(rs_ - np.median(rs_))) + 1e-12
    return cx, cy, float(z[rr8 <= 2].max() / sd)
LA = lumin(SV / 'sony_A_total_flat2d_v5.npy'); LB = lumin(SV / 'sony_B_total_v42.npy'); LV = lumin(AP / 'vixen_total.npy')
E = json.load(open(SV.parent / 'f1/F2_ESTRELLES.json')); rep = {}
for X, L in (('A', LA), ('B', LB)):
    rows = []
    for e in E[X]:
        ux, uy = f4.camp(MODEL, X, np.array([e['x']]), np.array([e['y']])); x1, y1 = e['x'] + ux[0], e['y'] + uy[0]
        cx = centroide(L, x1, y1); cv = centroide(LV, x1, y1)
        if cx and cv and cx[2] >= 6 and cv[2] >= 6:
            d = (cv[0] - cx[0], cv[1] - cx[1]); r_ = float(np.hypot(x1 - SOL[0], y1 - SOL[1]) / RS); a_ = float(np.degrees(np.arctan2(x1 - SOL[0], y1 - SOL[1])) % 360)
            rows.append(dict(id=e.get('id', e.get('nom')), x=round(x1, 1), y=round(y1, 1), r_Rsol=round(r_, 2), angle_des_de_baix=round(a_, 1), residu_px=[round(d[0], 2), round(d[1], 2)],
                             residu_abs_px=round(float(np.hypot(*d)), 2), sn_sony=round(cx[2], 1), sn_vixen=round(cv[2], 1), abans_px=round(float(np.hypot(e['ux'], e['uy'])), 2)))
    rows.sort(key=lambda z: -z['residu_abs_px']); m_ = np.array([z['residu_abs_px'] for z in rows])
    rep[X] = dict(n=len(rows), rms=round(float(np.sqrt(np.mean(m_ ** 2))), 2), rms_sense_la_pitjor=round(float(np.sqrt(np.mean(m_[1:] ** 2))), 2),
                  rms_sn_sony_ge_10=round(float(np.sqrt(np.mean(np.array([z['residu_abs_px'] for z in rows if z['sn_sony'] >= 10]) ** 2))), 2), estrelles=rows)
    log(X, json.dumps({k: v for k, v in rep[X].items() if k != 'estrelles'}), json.dumps(rows[:4], ensure_ascii=False))
json.dump(rep, open(OUT / 'F6E_ESTRELLES.json', 'w'), ensure_ascii=False, indent=1)
