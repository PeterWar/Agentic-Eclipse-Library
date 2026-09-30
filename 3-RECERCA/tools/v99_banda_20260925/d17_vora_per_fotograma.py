"""d17 (V99 banda) · On és el limbe REAL de cada fotograma? Per a cada fotograma i angle de posició lunar (15°), la distància D_obs (al cercle
del model) on ln(V_j/ref) creua −0,35 (T = 0,70): δ_j(PA). Si δ depèn del fotograma com cos(PA − φ) → error del centre del model d'aquell
fotograma; si és comú a tots com cos 2(PA − φ) → la Lluna observada no és un cercle (refracció diferencial o òptica). Només lectura."""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v99_banda_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32)
zona = (d >= -8) & (d < 60); X = xx[zona].astype(np.float64); Y = yy[zona].astype(np.float64); nF = len(fr); npx = int(zona.sum())
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
cls = np.array([classe(f['exposure']) for f in fr]); t = np.array([f['time'] for f in fr])
RAMPES = {'curts': (6.0, 9.0), 'mitjans': (5.0, 8.0), 'llargs': (6.0, 10.0)}
def smoothstep(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
V = np.zeros((nF, npx), np.float32); Wz = np.zeros_like(V); Dz = np.zeros_like(V); PA = np.zeros_like(V); C = np.zeros((nF, 2))
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    C[j] = (ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix], iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix])
    n_ = np.asarray(N[j, :, :, 1])[zona]; w_ = np.asarray(Wt[j, :, :, 1])[zona]
    V[j] = np.where(w_ > 0, n_ / np.maximum(w_, 1e-30), np.nan); Wz[j] = w_; Dz[j] = Dj[zona] + DR
    PA[j] = (np.degrees(np.arctan2(-(Y - C[j, 1]), X - C[j, 0])) + 360) % 360
S = np.stack([smoothstep(Dz[j], *RAMPES[cls[j]]) for j in range(nF)]); WS = Wz * S
ref = np.nansum(np.where(WS > 0, V * WS, 0), 0) / np.maximum(WS.sum(0), 1e-30); nref = (WS > 0).sum(0); okref = (nref >= 3) & (ref > 0)
DB = np.arange(-4, 12.01, 0.25); DC = DB[:-1] + 0.125; LLINDAR = -0.35
res = {}
for j in range(nF):
    ok = okref & (Wz[j] > 0) & np.isfinite(V[j]) & (V[j] > 0)
    L = np.log(np.maximum(V[j], 1e-30) / np.maximum(ref, 1e-30)); m_niv = ok & (Dz[j] >= 15) & (Dz[j] < 30)
    if m_niv.sum() < 500: continue
    L = L - np.median(L[m_niv]); fila = {}
    for a0 in range(0, 360, 15):
        sec = ok & (((PA[j] - a0) % 360) < 15)
        k = np.digitize(Dz[j][sec], DB) - 1; Ls = L[sec]; prof = np.full(DC.size, np.nan)
        for i in range(DC.size):
            mm = k == i
            if mm.sum() >= 25: prof[i] = np.median(Ls[mm])
        # primer creuament de −0,35 venint de fora cap endins: el D més gran amb perfil < llindar, seguit (cap enfora) de perfil ≥ llindar
        f = np.isfinite(prof)
        if f.sum() < 20 or not (prof[f] < LLINDAR).any() or not (prof[f] >= LLINDAR).any(): continue
        idx = np.flatnonzero(f); below = idx[prof[idx] < LLINDAR]; i1 = below.max(); nxt = idx[idx > i1]
        if nxt.size == 0: continue
        i2 = nxt[0]; x1, x2, y1, y2 = DC[i1], DC[i2], prof[i1], prof[i2]
        fila[a0 + 7.5] = round(float(x1 + (LLINDAR - y1) * (x2 - x1) / (y2 - y1)), 2)
    res[j] = dict(t=round(float(t[j]), 2), classe=cls[j], exposicio=fr[j]['exposure'], centre_model=C[j].round(3).tolist(), delta=fila)
    # ajust: δ(PA) = c0 + bx cos PA + by sin PA + a cos 2PA + b sin 2PA (si hi ha prou arc)
    if len(fila) >= 6:
        pa = np.radians(np.array(list(fila.keys()))); dv = np.array(list(fila.values()))
        A = np.stack([np.ones_like(pa), np.cos(pa), np.sin(pa), np.cos(2 * pa), np.sin(2 * pa)], 1)
        cov = np.degrees(pa.max() - pa.min())
        co, *_ = np.linalg.lstsq(A, dv, rcond=None); rr = dv - A @ co
        res[j]['ajust_c0_cos_sin_cos2_sin2'] = co.round(3).tolist(); res[j]['residu_rms'] = round(float(np.sqrt((rr ** 2).mean())), 3)
    print(j, round(float(t[j]), 1), cls[j], ' '.join(f"{int(k)}:{v:+.1f}" for k, v in fila.items()), flush=True)
(O / 'D17_VORA_PER_FOTOGRAMA.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
