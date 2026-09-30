"""f6 (V120, 29-09-2026) · PORTA DE LA REGLA 9 (postprocessat-corona): la Sony DEFORMADA (f5) contra la Vixen, mesurada de nou des de zero.
Mateixes mesures que el f1 (i que la porta demana), sobre les dades deformades:
  · RAIGS: detall azimutal del b1, correlació per finestres de 5° × 0,08 ln r (±0,6°, subpíxel, correlació ≥ 0,6); residu SISTEMÀTIC = mediana
    per caselles de 30° × tram de radi (el soroll de cada finestra no és un error de geometria);
  · ESTRELLES: centroides subpíxel a la Sony deformada (amb estrelles) i a la Vixen, S/N ≥ 6 a totes dues.
Les estrelles es tapen per a les mesures de detall amb discos (r = el radi d'halo de la V118, com a mínim 30 px) a les posicions velles i a les
transformades. Llindars de la porta (regla 9): mediana ≤ 0,5 px i màxim de les caselles ≤ 1 px a cada tram de radi on la finestra mesura amb
un soroll per sota d'1 px; estrelles, rms ≤ 1 px sense patró (on la mesura ho permet: el centroide de la Vixen té ~0,5 px de soroll a S/N 6).
Ús: f6_porta_regla9.py <carpeta_sony_v del f5> <carpeta_sortida>  → F6_PORTA.json"""
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
LA = lumin(SV / 'sony_A_total_flat2d_v5.npy'); LB = lumin(SV / 'sony_B_total_v42.npy'); LVs = lumin(S4 / 'vixen_starless.npy')
dv = np.load(AP / 'vixen_den.npy', mmap_mode='r'); mV = np.isfinite(LVs) & (np.asarray(dv) > 0)
# discs d'estrelles: posicions velles (d4, catàleg) i transformades (fA ≈ camp d'A per a la Sony combinada)
HALO = json.load(open(R / '4-RESULTATS/v118_20260929/ABV/b5/B5_AJUSTOS_ESTRELLES.json'))['halo']
pos = [(int(k.split(',')[0]), int(k.split(',')[1]), max(30, v['radi'])) for k, v in HALO.items()]
cat = json.load(open(R / '4-RESULTATS/v114_estrelles_20260928/CATALEG_ACCEPTAT_V114.json'))['stars']; pos += [(int(s['x']), int(s['y']), 30) for s in cat]
peu = np.zeros((H, W), bool)
for x, y, rp in pos:
    for X in (None, 'A', 'B'):
        if X: ux, uy = f4.camp(MODEL, X, np.array([x], float), np.array([y], float)); xc, yc = int(round(x + ux[0])), int(round(y + uy[0]))
        else: xc, yc = x, y
        y0, y1, x0, x1 = max(0, yc - rp), min(H, yc + rp + 1), max(0, xc - rp), min(W, xc + rp + 1); yy, xx = np.ogrid[y0:y1, x0:x1]
        peu[y0:y1, x0:x1] |= (xx - xc) ** 2 + (yy - yc) ** 2 <= rp * rp
# la taca de l'eix d'A, al seu lloc nou
gux, guy = f4.camp(MODEL, 'A', np.array([b1.GX]), np.array([b1.GY])); GXn, GYn = b1.GX + gux[0], b1.GY + guy[0]
yy_, xx_ = np.ogrid[:H, :W]
m = np.isfinite(LA) & np.isfinite(LB) & mV & ~peu & (np.hypot(xx_ - GXn, yy_ - GYn) > 320)
log('suport', round(float(m.mean()), 3))
PM = b1.polar(m.astype(np.float32)) > 0.999; den_c = {}
def gn(x, sr, st_):
    if (sr, st_) not in den_c: den_c[(sr, st_)] = b1.gcv(PM.astype(np.float32), sr, st_)
    den = den_c[(sr, st_)]; return b1.gcv(np.where(PM, x, 0).astype(np.float32), sr, st_) / np.maximum(den, 1e-6), den
def detall(L):
    x = np.where(PM, np.log(np.maximum(b1.polar(np.nan_to_num(L)), 1e-9)), 0).astype(np.float32); a, _ = gn(x, b1.SR, b1.S1); c, _ = gn(x, b1.SR, b1.S2)
    return np.where(PM, a - c, 0).astype(np.float32)
DS = 4
def redueix(X): return cv2.resize(X, (X.shape[1] // DS, X.shape[0] // DS), interpolation=cv2.INTER_AREA)
D = {n: redueix(detall(L)) for n, L in (('A', LA), ('B', LB), ('V', LVs))}; PMr = redueix(PM.astype(np.float32)) > 0.99
rho_red = b1.rho.reshape(-1, DS).mean(1); nt = b1.NT // DS; dth = 360.0 / nt
def finestres(Xp, Up, Vm):
    wt = int(round(5.0 / dth)); wr = int(round(0.08 / (b1.dr * DS))); ms = int(np.ceil(0.6 / dth)); pad = wt
    def box(z): zp = np.concatenate([z[:, -pad:], z, z[:, :pad]], 1); return cv2.boxFilter(zp, -1, (wt, wr), normalize=True, borderType=cv2.BORDER_REFLECT)[:, pad:-pad]
    uu = box(np.where(Vm, Up * Up, 0)); cor = []
    for s in range(-ms, ms + 1):
        xs = np.roll(Xp, -s, axis=1); vs = Vm & np.roll(Vm, -s, axis=1)
        num = box(np.where(vs, xs * Up, 0)); xx = box(np.where(vs, xs * xs, 0)); cov = box(vs.astype(np.float32))
        cor.append(np.where(cov > 0.9, num / np.sqrt(np.maximum(xx * uu, 1e-20)), np.nan))
    cor = np.nan_to_num(np.stack(cor), nan=-1); i = np.argmax(cor, 0); cmax = np.take_along_axis(cor, i[None], 0)[0]
    ii = np.clip(i, 1, 2 * ms - 1); y0, y1, y2 = [np.take_along_axis(cor, (ii + k)[None], 0)[0] for k in (-1, 0, 1)]
    dd = y0 - 2 * y1 + y2; sub = np.where(np.abs(dd) > 1e-9, 0.5 * (y0 - y2) / np.where(np.abs(dd) > 1e-9, dd, 1), 0); s = ii + sub - ms
    bo = (cmax >= 0.6) & (i > 0) & (i < 2 * ms) & Vm
    rows = np.arange(wr // 2, Xp.shape[0], max(wr // 2, 1)); cols = np.arange(wt // 2, Xp.shape[1], max(wt // 2, 1)); rr, cc = np.meshgrid(rows, cols, indexing='ij'); rr, cc = rr.ravel(), cc.ravel(); k = bo[rr, cc]
    return np.exp(rho_red[rr[k]]), cc[k] * 2 * np.pi / nt, -s[rr, cc][k] * dth * np.pi / 180, cmax[rr, cc][k]
porta = dict(guio=str(Path(__file__).relative_to(R)), raigs={}, estrelles={})
for X in ('A', 'B'):
    r_px, th, dtheta, cm = finestres(D[X], D['V'], PMr); upx = r_px * dtheta; tb = {}
    for lo, hi in ((1.3, 2), (2, 3), (3, 4.5), (4.5, 6), (6, 8)):
        k = (r_px >= lo * RS) & (r_px < hi * RS); meds = []
        for sct in range(12):
            kk = k & (np.floor(np.degrees(th) % 360 / 30) == sct)
            if kk.sum() >= 15: meds.append(np.median(upx[kk]))
        soroll = float(np.median(np.abs(upx[k] - np.median(upx[k])))) if k.sum() else None
        tb[f'{lo}-{hi}'] = dict(finestres=int(k.sum()), residu_px_mediana_max=[round(float(np.median(np.abs(meds))), 2), round(float(np.max(np.abs(meds))), 2)] if meds else None,
                               soroll_finestra_px=round(soroll, 2) if soroll is not None else None,
                               passa=bool(meds and np.median(np.abs(meds)) <= 0.5 and np.max(np.abs(meds)) <= 1.0) if (soroll is not None and soroll < 1.0) else 'no mesurable (soroll ≥ 1 px)')
    porta['raigs'][X] = tb; log(X, 'raigs', json.dumps(tb, ensure_ascii=False))
# estrelles: centroides a la Sony deformada (amb estrelles) i a la Vixen
sys.argv = [sys.argv[0], str(OUT)]
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
LV = lumin(AP / 'vixen_total.npy')
E = json.load(open(SV.parent / 'f1/F2_ESTRELLES.json'))
for X, L in (('A', LA), ('B', LB)):
    rows = []
    for e in E[X]:
        ux, uy = f4.camp(MODEL, X, np.array([e['x']]), np.array([e['y']])); x1, y1 = e['x'] + ux[0], e['y'] + uy[0]     # on ha de ser ara
        cx = centroide(L, x1, y1); cv = centroide(LV, x1, y1)
        if cx and cv and cx[2] >= 6 and cv[2] >= 6: rows.append((cv[0] - cx[0], cv[1] - cx[1], e['ux'], e['uy']))
    if rows:
        d = np.array([[r_[0], r_[1]] for r_ in rows]); d0 = np.array([[r_[2], r_[3]] for r_ in rows]); m_ = np.hypot(d[:, 0], d[:, 1])
        porta['estrelles'][X] = dict(n=len(rows), abans_rms_px=round(float(np.sqrt(np.mean(np.sum(d0 ** 2, 1)))), 2), despres_rms_px=round(float(np.sqrt(np.mean(m_ ** 2))), 2),
                                     despres_mediana_px=round(float(np.median(m_)), 2), despres_max_px=round(float(m_.max()), 2), mitjana_px=[round(float(d[:, 0].mean()), 2), round(float(d[:, 1].mean()), 2)])
    log(X, 'estrelles', porta['estrelles'].get(X))
porta['segons'] = round(time.time() - t0, 1); json.dump(porta, open(OUT / 'F6_PORTA.json', 'w'), ensure_ascii=False, indent=1); log('fet')
