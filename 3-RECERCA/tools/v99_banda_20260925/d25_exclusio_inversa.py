"""d25 (V99 banda) · EXCLUSIÓ INVERSA a dalt i a l'esquerra (PA 60–270), on la banda existeix: prova = fotogrames TARDANS (t > 80 s; curts
107–117 s i les ràfegues 82–105 s, la mateixa barreja d'exposicions que els primerencs que veuen la banda), estimació A amb rampa lo→lo+2,5 sobre
D_real; veritat B = fotogrames t < 70 s amb D_real ≥ 9. Post-matriu: G' i L'. Biaix = ln(A'/B') al calaix de D_real (pes mitjà) − el de 10–20 px.
Silueta comuna d'ordre 2 (D21_silueta_o2.npz). Porta de Codex: |biaix| ≤ 2 %. Només lectura."""
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
zona = (d >= -10) & (d < 60); X = xx[zona].astype(np.float64); Y = yy[zona].astype(np.float64); nF = len(fr); npx = int(zona.sum()); t = np.array([f['time'] for f in fr])
def smoothstep(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
Dr = np.zeros((nF, npx), np.float32); PA = np.zeros_like(Dr); V = np.zeros((nF, npx, 3), np.float32); W = np.zeros_like(V)
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    PA[j] = (np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360; Dr[j] = Dj[zona] + DR - np.interp(PA[j], pag, eg, period=360)
    for c in range(3):
        w = np.asarray(Wt[j, :, :, c])[zona]; n = np.asarray(N[j, :, :, c])[zona]; V[j, :, c] = np.where(w > 0, n / np.maximum(w, 1e-30), np.nan); W[j, :, c] = w
def post(E): P = np.einsum('ij,...j->...i', Mx, E * gn); return P[..., 1], (P[..., 0] + 2 * P[..., 1] + P[..., 2]) / 4
def mitjana(js, sfun):
    num = np.zeros((npx, 3)); den = np.zeros((npx, 3)); dm = np.zeros(npx); dw = np.zeros(npx); pm = np.zeros(npx)
    for j in js:
        s = sfun(j)
        for c in range(3):
            m = (W[j, :, c] > 0) & np.isfinite(V[j, :, c]) & (s > 0); w = np.where(m, W[j, :, c] * s, 0); num[:, c] += np.where(m, w * V[j, :, c], 0); den[:, c] += w
            if c == 1: dm += w * np.where(m, Dr[j], 0); dw += w; pm += w * np.where(m, np.cos(np.radians(PA[j])) + 1j * np.sin(np.radians(PA[j])), 0).real * 0
    return np.where((den > 0).all(1)[:, None], num / np.maximum(den, 1e-30), np.nan), np.where(dw > 0, dm / np.maximum(dw, 1e-30), np.nan)
PROVA = np.flatnonzero(t > 80); VERITAT = np.flatnonzero(t < 70)
EB, _ = mitjana(VERITAT, lambda j: (Dr[j] >= 9).astype(float)); GB, LB = post(EB)
jref = PROVA[len(PROVA) // 2]; PAref = PA[jref]   # PA lunar d'un fotograma tardà típic (la Lluna tardana es mou poc entre 82 i 117 s)
rep = {}
for lo in (3.5, 4.0, 4.5, 5.0):
    EA, Dmit = mitjana(PROVA, lambda j: smoothstep(Dr[j], lo, lo + 2.5)); GA, LA = post(EA); rep[f'{lo}'] = {}
    for a0 in range(60, 270, 30):
        sec = ((PAref - a0) % 360) < 30; row = {}
        for q, (A_, B_) in (('G', (GA, GB)), ('L', (LA, LB))):
            ok = sec & np.isfinite(A_) & np.isfinite(B_) & (A_ > 0) & (B_ > 0); ref = ok & (Dmit >= 10) & (Dmit < 20)
            if ref.sum() < 200: continue
            r0 = float(np.median(np.log(A_[ref] / B_[ref])))
            for k0 in np.arange(lo, lo + 2.51, 0.5):
                zz = ok & (Dmit >= k0) & (Dmit < k0 + 0.5)
                if zz.sum() >= 80: row[f'{q}{k0:.1f}'] = round(float(np.median(np.log(A_[zz] / B_[zz]))) - r0, 4)
        rep[f'{lo}'][f'{a0}-{a0+30}'] = row
    print('lo', lo); [print('  PA', s, ' '.join(f"{k}:{v:+.3f}" for k, v in r.items())) for s, r in rep[f'{lo}'].items()]
(O / 'D25_EXCLUSIO_INVERSA.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
