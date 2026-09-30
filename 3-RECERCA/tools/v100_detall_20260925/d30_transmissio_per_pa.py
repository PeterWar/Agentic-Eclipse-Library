"""d30 (V100 detall) · Transmissió de vora T(D_real, PA) per CLASSE i CANAL cru (R, G, B), mesurada amb la silueta d'ordre 2.
Per fotograma: ln(V_j / ref) − nivell del sector a D_real 8–14 px (ref = mitjana ponderada de TOTS els fotogrames amb D_real ≥ 9; el fotograma
mesurat mai no hi entra amb D_real < 9). PA lunar del fotograma. Calaixos: PA de 10° (finestra de 20°), D_real de 0,25 px de 0 a 8.
Èpoques separades: primerencs (t < 32 s, mesurables a la dreta), mitjans (80–106 s: ràfegues) i tardans (t > 106 s: curts finals); a dalt i a
l'esquerra només hi ha les dues últimes. Sortida: D30_T_per_PA.npz (lnT[epoca][classe][canal] → matriu PA×D, amb n) i D30 JSON amb la consistència
entre èpoques on se solapen. Només lectura de la dada."""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'
O = ARREL / '4-RESULTATS/v100_detall_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32)
zona = (d >= -12) & (d < 45); X = xx[zona].astype(np.float64); Y = yy[zona].astype(np.float64); nF = len(fr); npx = int(zona.sum())
t = np.array([f['time'] for f in fr]); ex = np.array([f['exposure'] for f in fr])
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
cls = np.array([classe(e) for e in ex]); epoca = np.where(t < 32, 'primerencs', np.where(t < 106, 'mitjans', 'tardans'))
Dr = np.zeros((nF, npx), np.float32); PA = np.zeros_like(Dr)
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    PA[j] = (np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360; Dr[j] = Dj[zona] + DR - np.interp(PA[j], pag, eg, period=360)
PAB = np.arange(0, 360, 10); DB = np.arange(0, 8.01, 0.25); out = {}; cons = {}
for c, nc in enumerate('RGB'):
    V = np.zeros((nF, npx), np.float32); W = np.zeros_like(V)
    for j in range(nF):
        w = np.asarray(Wt[j, :, :, c])[zona]; n = np.asarray(N[j, :, :, c])[zona]; V[j] = np.where(w > 0, n / np.maximum(w, 1e-30), np.nan); W[j] = w
    m9 = (Dr >= 9) & (W > 0) & np.isfinite(V); ref = np.where(m9, W * V, 0).sum(0) / np.maximum(np.where(m9, W, 0).sum(0), 1e-30); okr = (m9.sum(0) >= 3) & (ref > 0)
    L = np.where(okr[None] & (W > 0) & np.isfinite(V) & (V > 0), np.log(np.maximum(V, 1e-30) / np.maximum(ref, 1e-30)[None]), np.nan)
    for ep in ('primerencs', 'mitjans', 'tardans'):
        for cl in ('curts', 'mitjans', 'llargs'):
            js = np.flatnonzero((epoca == ep) & (cls == cl))
            if js.size == 0: continue
            Lj = L[js]; Dj_ = Dr[js]; Pj = PA[js]; M = np.full((PAB.size, DB.size), np.nan, np.float32); Nn = np.zeros((PAB.size, DB.size), np.int32)
            for ia, a in enumerate(PAB):
                sec = ((((Pj - a + 180) % 360) - 180) ** 2 < 100) & np.isfinite(Lj)   # finestra de ±10°
                ml = sec & (Dj_ >= 8) & (Dj_ < 14)
                if ml.sum() < 200: continue
                lv = np.median(Lj[ml]); kd = np.digitize(Dj_[sec], DB) - 1; Ls = Lj[sec] - lv
                for k in range(DB.size - 1):
                    q = Ls[kd == k]
                    if q.size >= 60: M[ia, k] = np.median(q); Nn[ia, k] = q.size
            out[f'{ep}|{cl}|{nc}'] = (M, Nn)
    print(nc, 'fet', flush=True)
# consistència entre èpoques (mateix PA i classe) a D 1,5–4
for key in out:
    ep, cl, nc = key.split('|')
    for ep2 in ('mitjans', 'tardans', 'primerencs'):
        k2 = f'{ep2}|{cl}|{nc}'
        if ep2 <= ep or k2 not in out: continue
        A_, B_ = out[key][0], out[k2][0]; sel = (DB >= 1.5) & (DB < 4); dif = (A_ - B_)[:, sel]; f = np.isfinite(dif)
        if f.sum() > 10: cons[f'{key} vs {ep2}'] = dict(n=int(f.sum()), mediana=round(float(np.nanmedian(dif)), 4), p90_abs=round(float(np.nanpercentile(np.abs(dif[f]), 90)), 4),
                                                        PA_solapats=[int(PAB[i]) for i in range(PAB.size) if np.isfinite(dif[i]).any()])
np.savez_compressed(O / 'D30_T_per_PA.npz', PA=PAB, D=DB, **{k.replace('|', '__'): v[0] for k, v in out.items()}, **{'n__' + k.replace('|', '__'): v[1] for k, v in out.items()})
(O / 'D30_CONSISTENCIA_EPOQUES.json').write_text(json.dumps(cons, ensure_ascii=False, indent=1))
for k, v in cons.items(): print(k, v['mediana'], v['p90_abs'], v['PA_solapats'][:12])
