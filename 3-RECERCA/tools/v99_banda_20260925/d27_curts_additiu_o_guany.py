"""d27 (V99 banda) · El desnivell dels fotogrames de 1/3200 s (d26: R −5,6 %, G −1,4 %, B −9,6 % respecte de la barreja): és un GUANY (constant en
ln) o un DESPLAÇAMENT additiu (nivell de negre: ln(V/ref) ∝ −a/ref, més fort on la corona és feble)? Per canal, la mediana de ln(V_j/ref) per
calaixos de brillantor de ref (D_real 10–200 px, fora del dèficit de vora), i ajust V_j = g·ref − a. Només lectura."""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v99_banda_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32)
zona = (d >= 5) & (d < 240); zona[::2, :] = False; zona[:, ::2] = False; nF = len(fr); npx = int(zona.sum()); ex = np.array([f['exposure'] for f in fr])
Dz = np.stack([np.asarray(Dm[j])[zona] + DR for j in range(nF)])
rep = {}
for c, nc in enumerate('RGB'):
    V = np.stack([np.where(np.asarray(Wt[j, :, :, c])[zona] > 0, np.asarray(N[j, :, :, c])[zona] / np.maximum(np.asarray(Wt[j, :, :, c])[zona], 1e-30), np.nan) for j in range(nF)])
    Wc = np.stack([np.asarray(Wt[j, :, :, c])[zona] for j in range(nF)]); ok = (Wc > 0) & np.isfinite(V) & (Dz >= 12) & (ex[:, None] > 0.003)   # referència: exposicions ≥ 1/250 s
    ref = np.nansum(np.where(ok, Wc * V, 0), 0) / np.maximum(np.where(ok, Wc, 0).sum(0), 1e-30); okr = (ok.sum(0) >= 3) & (ref > 0)
    for e in (0.0003125, 0.0005, 0.001, 0.002):
        js = np.flatnonzero(ex == e); vs = []; rs = []
        for j in js:
            m = okr & (Wc[j] > 0) & np.isfinite(V[j]) & (Dz[j] >= 12); vs.append(V[j][m]); rs.append(ref[m])
        v = np.concatenate(vs); r = np.concatenate(rs); q = np.quantile(r, np.linspace(0, 1, 11)); k = np.clip(np.digitize(r, q) - 1, 0, 9)
        prof = [(float(np.median(r[k == i])), float(np.median(np.log(np.maximum(v[k == i], 1e-30) / r[k == i])))) for i in range(10)]
        A = np.stack([r, -np.ones_like(r)], 1); g, a = np.linalg.lstsq(A, v, rcond=None)[0]
        rep[f'{nc}_{e:g}'] = dict(perfil_brillantor_lnratio=[(round(x, 1), round(y, 4)) for x, y in prof], guany=round(float(g), 4), additiu_a=round(float(a), 2), ref_mediana=round(float(np.median(r)), 1))
        print(nc, f'{e:g}', 'ln(V/ref) de fosc a clar:', ' '.join(f'{y:+.3f}' for _, y in prof), f'| g={g:.3f} a={a:.1f} (ref med {np.median(r):.0f})', flush=True)
(O / 'D27_CURTS_ADDITIU_O_GUANY.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
