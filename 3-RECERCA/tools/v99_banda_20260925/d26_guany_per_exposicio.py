"""d26 (V99 banda) · El nivell de cada TEMPS D'EXPOSICIÓ respecte de la barreja, lluny del limbe (D_real 15–40 px, on cap fotograma no té dèficit):
mediana de ln(V_j / ref) per exposició, per canal cru (R, G, B) i en post-matriu (G', L'), per sector (4 quadrants) i època. Si un temps
d'exposició té un desnivell constant (l'obturador a 1/3200 s no dura exactament 1/3200 s), a la vora de la banda, on només hi entren els
primers curts, apareix un graó. Només lectura."""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v99_banda_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
Mx = np.array(meta['matrix'], np.float64); gn = np.array(meta['gain'], np.float64)
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
S = np.load(O / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32)
zona = (d >= 0) & (d < 80); X = xx[zona].astype(np.float64); Y = yy[zona].astype(np.float64); th = (np.degrees(np.arctan2(-(Y - LY), X - LX)) + 360) % 360
nF = len(fr); npx = int(zona.sum()); t = np.array([f['time'] for f in fr]); ex = np.array([f['exposure'] for f in fr])
Dr = np.zeros((nF, npx), np.float32); V = np.zeros((nF, npx, 3), np.float32); W = np.zeros_like(V)
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    pa = (np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360; Dr[j] = Dj[zona] + DR - np.interp(pa, pag, eg, period=360)
    for c in range(3):
        w = np.asarray(Wt[j, :, :, c])[zona]; n = np.asarray(N[j, :, :, c])[zona]; V[j, :, c] = np.where(w > 0, n / np.maximum(w, 1e-30), np.nan); W[j, :, c] = w
num = np.zeros((npx, 3)); den = np.zeros((npx, 3))
for j in range(nF):
    for c in range(3):
        m = (W[j, :, c] > 0) & np.isfinite(V[j, :, c]) & (Dr[j] >= 15); num[:, c] += np.where(m, W[j, :, c] * V[j, :, c], 0); den[:, c] += np.where(m, W[j, :, c], 0)
ref = np.where((den > 0).all(1)[:, None], num / np.maximum(den, 1e-30), np.nan)
def post(E): P = np.einsum('ij,...j->...i', Mx, E * gn); return np.stack([P[..., 1], (P[..., 0] + 2 * P[..., 1] + P[..., 2]) / 4], -1)
refp = post(ref); rep = {}
for e in sorted(set(ex)):
    js = np.flatnonzero(ex == e); r = {'n_fotogrames': int(js.size), 't': [round(float(t[j]), 1) for j in js]}
    for nom, idx in (('R', 0), ('G', 1), ('B', 2), ("G'", 'p0'), ("L'", 'p1')):
        vals = {q: [] for q in ('dreta', 'dalt', 'esquerra', 'baix', 'tot')}
        for j in js:
            ok = (Dr[j] >= 15) & (Dr[j] < 40) & (W[j] > 0).all(1) & np.isfinite(V[j]).all(1) & np.isfinite(ref).all(1) & (ref > 0).all(1)
            if ok.sum() < 500: continue
            if isinstance(idx, int): lr = np.log(V[j, ok, idx] / ref[ok, idx])
            else:
                vp = post(V[j, ok]); k = int(idx[1]); g = (vp[:, k] > 0) & (refp[ok, k] > 0); lr = np.log(np.where(g, vp[:, k], np.nan) / np.where(g, refp[ok, k], np.nan))
            tq = th[ok]
            for q, (a0, a1) in dict(dreta=(315, 405), dalt=(45, 135), esquerra=(135, 225), baix=(225, 315)).items():
                s = (((tq - a0) % 360) < (a1 - a0)) & np.isfinite(lr)
                if s.sum() > 200: vals[q].append(float(np.median(lr[s])))
            vals['tot'].append(float(np.nanmedian(lr)))
        r[nom] = {q: round(float(np.median(v)), 4) if v else None for q, v in vals.items()}
    rep[f'{e:g}'] = r; print(f'{e:>10g} n={js.size:2d}', ' '.join(f"{k}:{r[k]['tot']:+.3f}" for k in ('R', 'G', 'B', "G'", "L'") if r[k]['tot'] is not None), '| G quadrants', r['G'], flush=True)
(O / 'D26_GUANY_PER_EXPOSICIO.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
