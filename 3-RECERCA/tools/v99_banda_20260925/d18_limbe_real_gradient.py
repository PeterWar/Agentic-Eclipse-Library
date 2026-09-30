"""d18 (V99 banda) · El limbe REAL de cada fotograma pel màxim del gradient radial de V (la vora de la Lluna convolucionada per la PSF),
sense referència: funciona també on la banda no té veritat neta (fotogrames primerencs a dalt i a l'esquerra).
Per fotograma j i angle de posició lunar (5°): perfil radial de V_j (mediana per calaix de 0,25 px de D_obs), lleugerament suavitzat,
i el D de màxim dV/dD dins de [−7, 9] px → e_j(PA). Es compara amb el creuament T = 0,70 de d17 on tots dos existeixen.
Sortida: D18_LIMBE_REAL.json (e_j per PA i fotograma) i D18_limbe_real.npz. Només lectura."""
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v99_banda_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32)
zona = (d >= -40) & (d < 40); X = xx[zona].astype(np.float64); Y = yy[zona].astype(np.float64); nF = len(fr)
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
cls = np.array([classe(f['exposure']) for f in fr]); t = np.array([f['time'] for f in fr])
DB = np.arange(-10, 12.01, 0.25); DC = DB[:-1] + 0.125; NPA = 72
E = np.full((nF, NPA), np.nan); PK = np.full((nF, NPA), np.nan); C = np.zeros((nF, 2))
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    C[j] = (ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix], iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix])
    n_ = np.asarray(N[j, :, :, 1])[zona]; w_ = np.asarray(Wt[j, :, :, 1])[zona]; D_ = Dj[zona] + DR
    ok = (w_ > 0) & (D_ >= DB[0]) & (D_ < DB[-1]); V_ = np.where(ok, n_ / np.maximum(w_, 1e-30), np.nan)
    pa = (np.degrees(np.arctan2(-(Y - C[j, 1]), X - C[j, 0])) + 360) % 360; ipa = (pa / (360 / NPA)).astype(int) % NPA; kd = np.digitize(D_, DB) - 1
    sel = ok & np.isfinite(V_); key = ipa[sel] * DC.size + kd[sel]; v = V_[sel]
    o = np.argsort(key); key = key[o]; v = v[o]; tall = np.searchsorted(key, np.arange(NPA * DC.size + 1))
    P = np.full(NPA * DC.size, np.nan)
    for q in range(NPA * DC.size):
        a, b = tall[q], tall[q + 1]
        if b - a >= 8: P[q] = np.median(v[a:b])
    P = P.reshape(NPA, DC.size)
    for k in range(NPA):
        p = P[k]; f = np.isfinite(p)
        if f.sum() < 0.8 * DC.size: continue
        pi = np.interp(DC, DC[f], p[f]); ps = gaussian_filter1d(pi, 1.0); g = np.gradient(ps, DC)
        w = (DC >= -7) & (DC <= 9); i = np.flatnonzero(w)[np.argmax(g[w])]
        if 0 < i < DC.size - 1 and g[i] > 0:
            y0_, y1_, y2_ = g[i - 1], g[i], g[i + 1]; den = y0_ - 2 * y1_ + y2_; sh = 0.5 * (y0_ - y2_) / den if den != 0 else 0
            E[j, k] = DC[i] + sh * 0.25
            fora = ps[(DC >= E[j, k] + 6) & (DC <= E[j, k] + 10)]; dins = ps[(DC >= E[j, k] - 10) & (DC <= E[j, k] - 6)]
            PK[j, k] = float((np.median(fora) - np.median(dins)) / max(np.median(fora), 1e-30)) if fora.size and dins.size else np.nan
    print(j, round(float(t[j]), 1), cls[j], 'e(PA) cada 30°:', ' '.join(f"{k*5}:{E[j,k]:+.1f}" for k in range(0, NPA, 6)), flush=True)
np.savez(O / 'D18_limbe_real.npz', E=E, contrast=PK, centre_model=C, t=t, cls=cls, pa=np.arange(NPA) * 360 / NPA + 2.5)
d17 = json.loads((O / 'D17_VORA_PER_FOTOGRAMA.json').read_text()); dif = {c: [] for c in ('curts', 'mitjans', 'llargs')}
for js, r in d17.items():
    j = int(js)
    for pa, dv in r['delta'].items():
        k = int(float(pa) // 5)
        if np.isfinite(E[j, k]): dif[r['classe']].append((float(pa), dv - E[j, k], r['t']))
rep = dict(nota='e = D_obs (px, respecte del cercle de presentació) del màxim de dV/dD per fotograma i PA de 5°; comparació amb el creuament T=0,70 de d17',
           e=[[None if not np.isfinite(v) else round(float(v), 2) for v in E[j]] for j in range(nF)], t=t.round(2).tolist(), classe=cls.tolist(),
           comparacio_d17={c: dict(n=len(v), mediana=round(float(np.median([x[1] for x in v])), 2) if v else None, p16_p84=np.percentile([x[1] for x in v], [16, 84]).round(2).tolist() if v else None,
                               per_PA={f'{int(p)}': round(float(np.median([x[1] for x in v if x[0] == p])), 2) for p in sorted(set(x[0] for x in v))}) for c, v in dif.items()})
(O / 'D18_LIMBE_REAL.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps(rep['comparacio_d17'], indent=0))
