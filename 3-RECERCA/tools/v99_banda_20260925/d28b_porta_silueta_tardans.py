"""d28b (V99 banda): el d28 amb la silueta feta NOMÉS amb fotogrames tardans (exclusió estricta per a la prova de la dreta). d28 (V99 banda, objecció de Codex 25-09) · La porta de biaix sobre el PRODUCTE EFECTIU: l'entrada real dels filtres i la validesa final.
  · Entrades: G' (base_G = c_G·G'), per a NRGF/RHEF/WOW/MGN/ACHF azimutals, i L_eff = (c0·R' + 2·c1·G' + c2·B')/4, per als ACHF isòtrops, amb els
    factors de l'a3c (A3C_FRANJA_SILUETA.json, escales c_F0/1/2).
  · Estimació de prova A amb la regla de l'a3c sobre el subconjunt de prova: rampa 4→6,5 sobre D_real (silueta d21), validesa
    Ws_G ≥ 1,5·W_CURT i NF ≥ 3 i els tres canals amb pes; VORA per azimut com l'a3c (el d més gran sense validesa + 0,25; màxim mòbil);
    distància a la vora = d − vora(θ).
  · Dues exclusions: DRETA (prova: t < 32 s; veritat: t > 40 s amb D_real ≥ 9) i INVERSA a dalt i a l'esquerra (prova: t > 80 s;
    veritat: t < 70 s amb D_real ≥ 9).
  · Biaix = mediana ln(A/B) per calaix de distància a la vora (0–0,5, 0,5–1, 1–2, 2–3, 3–5 px) − la mateixa a 10–20 px, per sector de 30° (azimut
    de la imatge). Porta de Codex: |biaix| ≤ 2 %. Només lectura."""
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import maximum_filter1d
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v99_banda_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
Mx = np.array(meta['matrix'], np.float64); gn = np.array(meta['gain'], np.float64)
esc = json.loads((O / 'B/lineal_v99_franja/A3C_FRANJA_SILUETA.json').read_text())['escales']; cF = [esc[f'c_F{c}'][0] for c in range(3)]
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
S = np.load(O / 'D21_silueta_o2_tardans.npz'); pag, eg = S['pa'], S['e']
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32); th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
zona = (d >= -15) & (d < 40); X = xx[zona].astype(np.float64); Y = yy[zona].astype(np.float64); dz = d[zona]; tz = th[zona]
nF = len(fr); npx = int(zona.sum()); t = np.array([f['time'] for f in fr]); ex = np.array([f['exposure'] for f in fr])
def smoothstep(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
Dr = np.zeros((nF, npx), np.float32); V = np.zeros((nF, npx, 3), np.float32); W = np.zeros_like(V)
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    pa = (np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360; Dr[j] = Dj[zona] + DR - np.interp(pa, pag, eg, period=360)
    for c in range(3):
        w = np.asarray(Wt[j, :, :, c])[zona]; n = np.asarray(N[j, :, :, c])[zona]; V[j, :, c] = np.where(w > 0, n / np.maximum(w, 1e-30), np.nan); W[j, :, c] = w
curts = np.flatnonzero(ex <= 1 / 800); _wc = np.asarray(Wt[curts[0], ::7, ::7, 1]); W_CURT = float(np.median(_wc[_wc > 0]))
def estima(js, sfun):
    num = np.zeros((npx, 3)); den = np.zeros((npx, 3)); nf = np.zeros(npx, np.int32)
    for j in js:
        s = sfun(j)
        for c in range(3):
            m = (W[j, :, c] > 0) & np.isfinite(V[j, :, c]) & (s > 0); w = np.where(m, W[j, :, c] * s, 0); num[:, c] += np.where(m, w * V[j, :, c], 0); den[:, c] += w
            if c == 1: nf += (w > 0)
    E = np.where(den > 0, num / np.maximum(den, 1e-30), 0); P = np.einsum('ij,...j->...i', Mx, E * gn)
    valid = (den[:, 1] >= 1.5 * W_CURT) & (nf >= 3) & (den > 0).all(1) & (P[:, 1] > 0)
    G = P[:, 1]; L = (cF[0] * P[:, 0] + 2 * cF[1] * P[:, 1] + cF[2] * P[:, 2]) / 4
    return G, L, valid
def vora(valid):
    NBZ = 1440; ib = (tz / 360 * NBZ).astype(int) % NBZ; z = (dz > -15) & (dz < 20); dm = np.full(NBZ, np.nan)
    o = np.argsort(ib[z]); ibs = ib[z][o]; ds = dz[z][o]; vs = valid[z][o]; tl = np.searchsorted(ibs, np.arange(NBZ + 1))
    for k in range(NBZ):
        dd_, vv_ = ds[tl[k]:tl[k + 1]], vs[tl[k]:tl[k + 1]]; bad = dd_[~vv_]; dm[k] = (bad.max() + 0.25) if bad.size else (dd_.min() if dd_.size else np.nan)
    ok = np.isfinite(dm); dm[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), dm[ok], period=NBZ); dm = maximum_filter1d(dm, 5, mode='wrap')
    return dz - dm[ib]
rep = {}
for nom, prova, veritat in (('dreta', np.flatnonzero(t < 32), np.flatnonzero(t > 40)), ('inversa', np.flatnonzero(t > 80), np.flatnonzero(t < 70))):
    GA, LA, vA = estima(prova, lambda j: smoothstep(Dr[j], 4.0, 6.5)); GB, LB, vB = estima(veritat, lambda j: (Dr[j] >= 9).astype(float))
    dv = vora(vA); rep[nom] = {}
    for a0 in range(0, 360, 30):
        sec = (((tz - a0) % 360) < 30) & vA & vB & (dv >= 0); row = {}
        for q, (A_, B_) in (("G'", (GA, GB)), ('L_eff', (LA, LB))):
            ok = sec & (A_ > 0) & (B_ > 0); ref = ok & (dv >= 10) & (dv < 20)
            if ref.sum() < 200: continue
            r0 = float(np.median(np.log(A_[ref] / B_[ref])))
            for lo, hi in ((0, 0.5), (0.5, 1), (1, 2), (2, 3), (3, 5)):
                zz = ok & (dv >= lo) & (dv < hi)
                if zz.sum() >= 60: row[f'{q} {lo}-{hi}'] = round(float(np.median(np.log(A_[zz] / B_[zz]))) - r0, 4)
        if row: rep[nom][f'{a0}-{a0+30}'] = row
    print(nom); [print('  ', s, ' '.join(f'{k}:{v:+.3f}' for k, v in r.items())) for s, r in rep[nom].items()]
pitjor = {n: min(((v, s, k) for s, r in rep[n].items() for k, v in r.items()), default=None) for n in rep}
rep['pitjor'] = {n: dict(biaix=p[0], sector=p[1], calaix=p[2]) for n, p in pitjor.items() if p}; rep['factors_cF'] = cF
print('pitjor', rep['pitjor'])
(O / 'D28_PORTA_PRODUCTE_EFECTIU_silueta_tardans.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
