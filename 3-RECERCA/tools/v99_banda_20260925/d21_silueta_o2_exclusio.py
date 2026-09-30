"""d21 (V99 banda, pla de Codex 25-09) · (1) Silueta d'ORDRE 2 comuna, sense les observacions primerenques (t < 40 s) a PA 110–250 (la Lluna hi és
a 1,6–8 px de la fotosfera: cromosfera). (2) Silueta d'exclusió estricta: NOMÉS fotogrames tardans (t > 40 s), per provar els primerencs.
(3) Exclusió a la dreta amb el conjunt de prova = TOTS els fotogrames primerencs (t < 32 s; curts, mitjans i llargs, amb els seus pesos LDIC reals:
la situació de la banda de dalt), sense correcció fotomètrica, per a diverses rampes sobre D_real. Veritat B = altres fotogrames amb D_real ≥ 9.
Biaix d'anell = mediana ln(A/B) al calaix de D_real − la mateixa a D_real 10–20 (desnivell entre grups de fotogrames, que a la imatge es barregen).
També per canal R, G, B (abans de la matriu). Porta de Codex: |biaix| ≤ 2 % per sector validable. Només lectura."""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v99_banda_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
cls = np.array([classe(f['exposure']) for f in fr]); t = np.array([f['time'] for f in fr]); exps = np.array([f['exposure'] for f in fr]); nF = len(fr)
z = np.load(O / 'D18_limbe_real.npz', allow_pickle=True); E18 = z['E']; PAc = z['pa']
d17 = json.loads((O / 'D17_VORA_PER_FOTOGRAMA.json').read_text()); d18 = json.loads((O / 'D18_LIMBE_REAL.json').read_text())
off = {c: d18['comparacio_d17'][c]['mediana'] for c in ('mitjans', 'llargs')}; off['curts'] = float(np.mean([off['mitjans'], off['llargs']]))
def observacions(filtre):
    o = []
    for j in range(nF):
        if exps[j] > 1.01: continue
        for k in range(PAc.size):
            if np.isfinite(E18[j, k]) and filtre(j, PAc[k]): o.append((PAc[k], E18[j, k], j))
    for js, r in d17.items():
        for pa, dv in r['delta'].items():
            if filtre(int(js), float(pa)): o.append((float(pa), dv - off[r['classe']], int(js)))
    return np.array(o)
def disseny(pa, n):
    a = np.radians(pa); cols = [np.ones_like(a)]
    for k in range(1, n + 1): cols += [np.cos(k * a), np.sin(k * a)]
    return np.stack(cols, 1)
def ajust(o, n):
    A = disseny(o[:, 0], n); y = o[:, 1]; w = np.ones_like(y)
    for _ in range(10):
        co = np.linalg.lstsq(A * w[:, None], y * w, rcond=None)[0]; r = y - A @ co; s = 1.4826 * np.median(np.abs(r)) + 1e-6; w = 1 / np.maximum(1, np.abs(r) / (2.5 * s))
    return co, s
cromo = lambda j, pa: t[j] < 40 and 110 <= pa <= 250
o_tot = observacions(lambda j, pa: not cromo(j, pa)); o_tard = observacions(lambda j, pa: t[j] > 40)
co2, s2 = ajust(o_tot, 2); co4, s4 = ajust(o_tot, 4); co2t, s2t = ajust(o_tard, 2)
# validació creuada per blocs de fotogrames (5 plecs): error de predicció de l'ordre 2 i del 4
rng = np.random.default_rng(0); plec = rng.permutation(nF) % 5; err = {2: [], 4: []}
for f in range(5):
    tr = o_tot[plec[o_tot[:, 2].astype(int)] != f]; te = o_tot[plec[o_tot[:, 2].astype(int)] == f]
    for n in (2, 4):
        c_, _ = ajust(tr, n); err[n].append(np.median(np.abs(te[:, 1] - disseny(te[:, 0], n) @ c_)))
pag = np.arange(0, 360, 0.25); e2 = disseny(pag, 2) @ co2; e4 = disseny(pag, 4) @ co4; e2t = disseny(pag, 2) @ co2t
rep = dict(coef_o2=co2.tolist(), coef_o4=co4.tolist(), coef_o2_tardans=co2t.tolist(), dispersio_o2=s2, dispersio_o4=s4,
           error_prediccio_blocs_mediana_abs={f'ordre{n}': round(float(np.mean(v)), 3) for n, v in err.items()},
           max_dif_o2_o4=round(float(np.abs(e2 - e4).max()), 3), dif_o2_tardans_menys_o2={f'{a}': round(float(e2t[a * 4] - e2[a * 4]), 2) for a in range(0, 360, 30)},
           e_o2={f'{a}': round(float(e2[a * 4]), 2) for a in range(0, 360, 15)})
print(json.dumps({k: v for k, v in rep.items() if k != 'e_o2'}, indent=0)); print('e_o2', rep['e_o2'])
np.savez(O / 'D21_silueta_o2.npz', pa=pag, e=e2, coef=co2); np.savez(O / 'D21_silueta_o2_tardans.npz', pa=pag, e=e2t, coef=co2t)
# --- (3) exclusió a la dreta amb tots els primerencs
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32); th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
caixa = (d > -12) & (d < 40) & ((th >= 280) | (th < 65)); ys, xs = np.nonzero(caixa); sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
YY = yy[sl].astype(np.float64); XX = xx[sl].astype(np.float64); hb, wb = YY.shape; tt = th[sl]
PROVA = np.flatnonzero(t < 32); ALTRES = np.flatnonzero(t > 40)
def smoothstep(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
Dr = {}; V = {}; W = {}
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    pa = (np.degrees(np.arctan2(-(YY - cy), XX - cx)) + 360) % 360; Dr[j] = Dj[sl] + DR - np.interp(pa.ravel(), pag, e2t, period=360).reshape(hb, wb)
    for c in range(3):
        w = np.asarray(Wt[j, :, :, c])[sl].astype(np.float64); n = np.asarray(N[j, :, :, c])[sl].astype(np.float64)
        V[j, c] = np.where(w > 0, n / np.maximum(w, 1e-30), np.nan); W[j, c] = w
RAMP_A = {'curts': (6.0, 9.0), 'mitjans': (5.0, 8.0), 'llargs': (6.0, 10.0)}
def mitjana(js, c, sfun):
    num = np.zeros((hb, wb)); den = np.zeros((hb, wb)); dm = np.zeros((hb, wb))
    for j in js:
        s = sfun(j); m = (W[j, c] > 0) & np.isfinite(V[j, c]) & (s > 0); w = np.where(m, W[j, c] * s, 0)
        num += np.where(m, w * V[j, c], 0); den += w; dm += w * np.where(m, Dr[j], 0)
    return np.where(den > 0, num / np.maximum(den, 1e-30), np.nan), den, np.where(den > 0, dm / np.maximum(den, 1e-30), np.nan)
res = {}
for c in range(3):
    B, wB, _ = mitjana(ALTRES, c, lambda j: (Dr[j] >= 9).astype(float))
    for nom, (lo, hi) in {'3-5.5': (3, 5.5), '3.5-6': (3.5, 6), '4-6.5': (4, 6.5), '4.5-7': (4.5, 7)}.items():
        A, wA, Dmit = mitjana(PROVA, c, lambda j: smoothstep(Dr[j], lo, hi)); key = f'{"RGB"[c]}_{nom}'; res[key] = {}
        for sn, (a0, a1) in {'280-330': (280, 330), '330-15': (330, 375), '15-65': (15, 65)}.items():
            sec = (((tt - a0) % 360) < (a1 - a0)) & np.isfinite(A) & np.isfinite(B) & (A > 0) & (B > 0) & (wB > 0)
            ref = sec & (Dmit >= 10) & (Dmit < 20); r0 = float(np.median(np.log(A[ref] / B[ref]))) if ref.sum() > 300 else np.nan; row = {'desnivell_10_20': round(r0, 4)}
            for k0 in np.arange(lo, lo + 4.01, 0.5):
                zz = sec & (Dmit >= k0) & (Dmit < k0 + 0.5)
                if zz.sum() >= 100: row[f'{k0:.1f}'] = round(float(np.median(np.log(A[zz] / B[zz]))) - r0, 4)
            res[key][sn] = row
        if c == 1 or nom == '3.5-6': print(key, res[key], flush=True)
rep['exclusio_dreta_primerencs'] = res
(O / 'D21_SILUETA_O2_EXCLUSIO.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
