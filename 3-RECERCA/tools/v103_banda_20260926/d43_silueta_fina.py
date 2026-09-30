"""d43 (V103/V104 banda) · SILUETA FINA per angle: el limbe real de cada fotograma mitjà i llarg pel màxim del gradient radial (com d18),
però a 2° (180 calaixos) i amb calaixos radials de 0,5 px, i el RESIDU respecte de la silueta d'ordre 2 (D21) com a candidat a RELLEU del
limbe lunar (fix en coordenades lunars: PA respecte del centre del model de cada fotograma). Prova de reproductibilitat: meitats temporals
(t < 60 s contra t > 60 s) i dispersió per calaix. Si el residu és reproduïble, e_fina = e_o2 + suavitzat(residu) (finestra de 3 calaixos).
Sortida: 4-RESULTATS/v103_banda_20260926/D43_SILUETA_FINA.json i D43_silueta_fina.npz (pa, e: la silueta fina en el format de D21, i e_o2, residu, meitats)."""
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'; O = ARREL / '4-RESULTATS/v103_banda_20260926'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32)
zona = (d >= -40) & (d < 40); X = xx[zona].astype(np.float64); Y = yy[zona].astype(np.float64); nF = len(fr)
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
cls = np.array([classe(f['exposure']) for f in fr]); t = np.array([f['time'] for f in fr])
NPA = 180; DB = np.arange(-10, 12.01, 0.5); DC = DB[:-1] + 0.25
E = np.full((nF, NPA), np.nan); C = np.zeros((nF, 2)); PAC = np.arange(NPA) * 360 / NPA + 1.0
for j in range(nF):
    if cls[j] == 'curts': continue
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
        if b - a >= 5: P[q] = np.median(v[a:b])
    P = P.reshape(NPA, DC.size)
    for k in range(NPA):
        p = P[k]; f = np.isfinite(p)
        if f.sum() < 0.8 * DC.size: continue
        pi = np.interp(DC, DC[f], p[f]); ps = gaussian_filter1d(pi, 1.0); g = np.gradient(ps, DC)
        w = (DC >= -7) & (DC <= 9); i = np.flatnonzero(w)[np.argmax(g[w])]
        if 0 < i < DC.size - 1 and g[i] > 0:
            y0_, y1_, y2_ = g[i - 1], g[i], g[i + 1]; den = y0_ - 2 * y1_ + y2_; sh = 0.5 * (y0_ - y2_) / den if den != 0 else 0
            E[j, k] = DC[i] + sh * 0.5
    print(j, round(float(t[j]), 1), cls[j], 'calaixos amb vora:', int(np.isfinite(E[j]).sum()), flush=True)
# residu respecte de l'ordre 2, per fotograma i calaix (el PA és el del centre del model del fotograma, com a l'a3c)
eo2 = np.interp(PAC, pag, eg, period=360); Rj = E - eo2[None, :]
usa = np.isfinite(Rj); med = np.nanmedian(np.where(usa, Rj, np.nan), axis=0); n = usa.sum(0); mad = np.nanmedian(np.abs(np.where(usa, Rj, np.nan) - med[None, :]), axis=0) * 1.4826
h1 = (t < 60)[:, None] & usa; h2 = (t >= 60)[:, None] & usa
m1 = np.nanmedian(np.where(h1, Rj, np.nan), axis=0); m2 = np.nanmedian(np.where(h2, Rj, np.nan), axis=0)
okh = np.isfinite(m1) & np.isfinite(m2) & (h1.sum(0) >= 3) & (h2.sum(0) >= 3)
rho = float(np.corrcoef(m1[okh], m2[okh])[0, 1]) if okh.sum() > 10 else None
# per sectors: reproductibilitat i amplitud del residu
sect = {}
for a0 in range(0, 360, 60):
    z = okh & (PAC >= a0) & (PAC < a0 + 60)
    sect[f'{a0}-{a0+60}'] = dict(n_calaixos=int(z.sum()), rho_meitats=round(float(np.corrcoef(m1[z], m2[z])[0, 1]), 3) if z.sum() > 6 else None,
                                 rms_residu_px=round(float(np.sqrt(np.nanmean(med[z] ** 2))), 3) if z.any() else None, mad_p50_px=round(float(np.nanmedian(mad[z])), 3) if z.any() else None,
                                 dif_meitats_rms_px=round(float(np.sqrt(np.mean((m1[z] - m2[z]) ** 2))), 3) if z.any() else None)
# silueta fina: e_o2 + residu suavitzat (mediana de 3 calaixos i gaussiana d'1 calaix), només on hi ha ≥ 4 fotogrames; on no, 0 (l'ordre 2)
r_ok = np.isfinite(med) & (n >= 4); r_ = np.where(r_ok, med, 0.0); r_ = median_filter(r_, size=3, mode='wrap'); r_ = gaussian_filter1d(r_, 1.0, mode='wrap')
e_fina = eo2 + r_
np.savez(O / 'D43_silueta_fina.npz', pa=PAC, e=e_fina, e_o2=eo2, residu=r_, residu_cru=med, n=n, mad=mad, m1=m1, m2=m2, E=E, t=t, cls=cls)
rep = dict(nota='residu = e_j(PA) − e_o2(PA) del màxim de dV/dD (mitjans i llargs), 2°, calaixos radials 0,5 px; meitats t<60 / t≥60', n_fotogrames=int((cls != 'curts').sum()),
           rho_meitats_global=None if rho is None else round(rho, 3), rms_residu_global_px=round(float(np.sqrt(np.nanmean(med[r_ok] ** 2))), 3), sectors=sect,
           residu_suavitzat_per_15=[dict(pa=int(a), residu=round(float(r_[int(a / 2)]), 2), n=int(n[int(a / 2)]), mad=round(float(mad[int(a / 2)]), 2) if np.isfinite(mad[int(a / 2)]) else None) for a in range(0, 360, 15)])
(O / 'D43_SILUETA_FINA.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print('rho meitats global', rho, '· rms residu', rep['rms_residu_global_px']); print(json.dumps(sect, ensure_ascii=False)); print(' '.join(f"{x['pa']}:{x['residu']:+.2f}({x['n']})" for x in rep['residu_suavitzat_per_15']))
