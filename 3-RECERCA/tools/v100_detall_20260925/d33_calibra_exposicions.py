"""d33 (V100 detall; pas 1 del pla de Codex) · CALIBRACIÓ RELATIVA de cada temps d'exposició i canal, lluny del limbe (D_real ≥ 12 px, fins a
d = 250 px): V_j = g_e·ref + a_e (guany i nivell de negre) respecte de la referència neta (mitjana ponderada de TOTS els fotogrames amb D_real ≥ 12,
sense el fotograma mesurat: referència «deixa-un-fora» aproximada restant-ne la contribució). Ajust en la meitat PARELL dels fotogrames de cada
exposició i validació en la SENAR (mostra reservada), per calaixos de brillantor (desenes de ref): residu ln(V_corregit/ref) sense tendència?
Porta de Codex: residus sense tendència amb brillantor ni exposició, |biaix| ≤ 2 % a la mostra reservada. Sortida: CALIBRACIO_EXPOSICIONS.json."""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'
O = ARREL / '4-RESULTATS/v100_detall_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - LX, yy - LY) - RL
zona = (d >= 5) & (d < 250); zona[1::2, :] = False; zona[:, 1::2] = False      # 1 de cada 4 píxels (la dada és correlacionada a 1 px)
X = xx[zona].astype(np.float64); Y = yy[zona].astype(np.float64); nF = len(fr); npx = int(zona.sum()); ex = np.array([f['exposure'] for f in fr]); t = np.array([f['time'] for f in fr])
Dr = np.zeros((nF, npx), np.float32)
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    pa = (np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360; Dr[j] = Dj[zona] + DR - np.interp(pa, pag, eg, period=360)
rep = {}
for c, nc in enumerate('RGB'):
    V = np.zeros((nF, npx), np.float32); W = np.zeros_like(V)
    for j in range(nF):
        w = np.asarray(Wt[j, :, :, c])[zona]; n = np.asarray(N[j, :, :, c])[zona]; V[j] = np.where(w > 0, n / np.maximum(w, 1e-30), np.nan); W[j] = w
    m = (Dr >= 12) & (W > 0) & np.isfinite(V); SW = np.where(m, W, 0).sum(0); SV = np.where(m, W * V, 0).sum(0)
    for e in sorted(set(ex)):
        js = np.flatnonzero(ex == e); r = {}
        for part, sel in (('ajust_parells', js[0::2]), ('valida_senars', js[1::2])):
            vs, rs = [], []
            for j in sel:
                mj = m[j]; sw = SW - np.where(mj, W[j], 0); sv = SV - np.where(mj, W[j] * V[j], 0)   # referència sense el fotograma j
                ok = mj & (sw > 0); ref = sv[ok] / sw[ok]; vs.append(V[j][ok]); rs.append(ref)
            if not vs or sum(v.size for v in vs) < 2000: continue
            r[part] = (np.concatenate(vs), np.concatenate(rs))
        if 'ajust_parells' not in r: continue
        v, rf = r['ajust_parells']; g_, a_ = np.linalg.lstsq(np.stack([rf, -np.ones_like(rf)], 1), v, rcond=None)[0]   # V = g·ref − a
        out = dict(n_fotogrames=int(js.size), guany=round(float(g_), 5), nivell_negre=round(float(a_), 2), ref_mediana=round(float(np.median(rf)), 1))
        for part, (v, rf) in r.items():
            q = np.quantile(rf, np.linspace(0, 1, 11)); k = np.clip(np.digitize(rf, q) - 1, 0, 9)
            cru = [round(float(np.median(np.log(np.maximum(v[k == i], 1e-30) / rf[k == i]))), 4) for i in range(10)]
            vc = (v + a_) / g_; cor = [round(float(np.median(np.log(np.maximum(vc[k == i], 1e-30) / rf[k == i]))), 4) for i in range(10)]
            out[part] = dict(ln_V_ref_cru_per_desena=cru, ln_V_ref_corregit_per_desena=cor, pitjor_corregit=max(cor, key=abs))
        rep[f'{nc}_{e:g}'] = out
        print(nc, f'{e:>9g}', f'g={g_:.4f} a={a_:8.1f}', 'reservada corregit:', out.get('valida_senars', {}).get('ln_V_ref_corregit_per_desena'), flush=True)
(O / 'CALIBRACIO_EXPOSICIONS.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
