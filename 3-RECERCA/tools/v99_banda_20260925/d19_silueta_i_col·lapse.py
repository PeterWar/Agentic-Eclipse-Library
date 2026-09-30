"""d19 (V99 banda) · (1) La silueta real de la Lluna respecte del cercle de presentació, e(PA), comuna a tots els fotogrames:
mediana per PA (5°) de les vores pel màxim del gradient (d18; mitjans i llargs ≤ 1 s) i dels creuaments T = 0,70 de d17 menys el seu desplaçament
mesurat respecte del gradient (per classe); ajust periòdic suau (Fourier fins a l'ordre 4, robust). Comprovació de deriva temporal
(primerencs contra tardans). (2) El COL·LAPSE: ln T per classe, època i sector amb D_real = D_obs − e(PA_j). Si les corbes coincideixen,
el dèficit era geometria (la silueta) + la PSF (comuna). Només lectura."""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v99_banda_20260925'
z = np.load(O / 'D18_limbe_real.npz', allow_pickle=True); E = z['E']; t = z['t']; cls = z['cls']; PAc = z['pa']; NPA = PAc.size
d17 = json.loads((O / 'D17_VORA_PER_FOTOGRAMA.json').read_text()); d18 = json.loads((O / 'D18_LIMBE_REAL.json').read_text())
off = {c: d18['comparacio_d17'][c]['mediana'] for c in ('mitjans', 'llargs')}; off['curts'] = float(np.mean([off['mitjans'], off['llargs']]))
exps = np.array([0.0] * len(t))
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; exps = np.array([f['exposure'] for f in fr])
obs = []   # (pa, e, t, font)
for j in range(len(t)):
    if exps[j] > 1.01: continue
    for k in range(NPA):
        if np.isfinite(E[j, k]): obs.append((PAc[k], E[j, k], t[j], 0))
for js, r in d17.items():
    for pa, dv in r['delta'].items():
        pa = float(pa)
        if r['classe'] == 'curts' and r['t'] < 32 and 140 <= pa <= 210: continue   # esquerra primerenca: la referència és el mateix fotograma (vegeu d17)
        obs.append((pa, dv - off[r['classe']], r['t'], 1))
obs = np.array(obs)
def disseny(pa, n=4):
    a = np.radians(pa); cols = [np.ones_like(a)]
    for k in range(1, n + 1): cols += [np.cos(k * a), np.sin(k * a)]
    return np.stack(cols, 1)
def ajust(o, n=4):
    A = disseny(o[:, 0], n); y = o[:, 1]; w = np.ones_like(y)
    for _ in range(8):
        co = np.linalg.lstsq(A * w[:, None], y * w, rcond=None)[0]; r = y - A @ co; s = 1.4826 * np.median(np.abs(r)) + 1e-6; w = 1 / np.maximum(1, np.abs(r) / (2.5 * s))
    return co, r, s
co, r, s = ajust(obs)
pag = np.arange(0, 360, 0.25); eg = disseny(pag) @ co
prim = obs[obs[:, 2] < 40]; tard = obs[obs[:, 2] > 80]
cop, rp, _ = ajust(prim, 2) if len(prim) > 30 else (None, None, None); cot, rt, _ = ajust(tard, 2) if len(tard) > 30 else (None, None, None)
# deriva: residus de cada època respecte de l'ajust comú, per PA
der = {}
for nom, oo in (('primerencs_t<40', prim), ('tardans_t>80', tard)):
    rr = oo[:, 1] - disseny(oo[:, 0]) @ co; der[nom] = {f'{a}': round(float(np.median(rr[((oo[:, 0] - a) % 360) < 30])), 2) for a in range(0, 360, 30) if (((oo[:, 0] - a) % 360) < 30).sum() >= 5}
print('silueta e(PA) cada 15°:', ' '.join(f"{a}:{eg[int(a*4)]:+.2f}" for a in range(0, 360, 15)))
print('coef (c0, cos1, sin1, cos2, sin2, ...)', co.round(3), 'dispersió robusta', round(s, 2), 'n', len(obs))
print('deriva per època (residu mediana, px):', der)
np.savez(O / 'D19_silueta.npz', pa=pag, e=eg, coef=co)
# (2) col·lapse
meta = json.loads((LF / 'METADATA.json').read_text()); by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32)
zona = (d >= -8) & (d < 60); X = xx[zona].astype(np.float64); Y = yy[zona].astype(np.float64); nF = len(fr); npx = int(zona.sum())
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
cl = np.array([classe(f['exposure']) for f in fr]); RAMPES = {'curts': (6.0, 9.0), 'mitjans': (5.0, 8.0), 'llargs': (6.0, 10.0)}
def smoothstep(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
V = np.zeros((nF, npx), np.float32); Wz = np.zeros_like(V); Dz = np.zeros_like(V); Dr = np.zeros_like(V); PA = np.zeros_like(V)
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    n_ = np.asarray(N[j, :, :, 1])[zona]; w_ = np.asarray(Wt[j, :, :, 1])[zona]
    V[j] = np.where(w_ > 0, n_ / np.maximum(w_, 1e-30), np.nan); Wz[j] = w_; Dz[j] = Dj[zona] + DR
    PA[j] = (np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360; Dr[j] = Dz[j] - np.interp(PA[j], pag, eg, period=360)
# referència: la selecció de la V98 (rampes sobre D_obs), independent de la silueta
S = np.stack([smoothstep(Dz[j], *RAMPES[cl[j]]) for j in range(nF)]); WS = Wz * S
ref = np.nansum(np.where(WS > 0, V * WS, 0), 0) / np.maximum(WS.sum(0), 1e-30); okref = ((WS > 0).sum(0) >= 3) & (ref > 0)
lr = np.where(okref[None] & (Wz > 0) & np.isfinite(V) & (V > 0), np.log(np.maximum(V, 1e-30) / np.maximum(ref, 1e-30)[None]), np.nan)
ep = np.where(np.array([f['time'] for f in fr]) < 40, 'prim', 'tard'); DB = np.arange(-1, 10.01, 0.5); rep = dict(silueta_coef=co.tolist(), dispersio_px=s, deriva=der, T={})
for c in RAMPES:
    for e_ in ('prim', 'tard'):
        js = np.flatnonzero((cl == c) & (ep == e_))
        if js.size == 0: continue
        L = lr[js]; D_ = Dr[js]; P_ = PA[js]; mn = np.isfinite(L) & (D_ >= 12) & (D_ < 30)
        if mn.sum() < 1000: continue
        L = L - np.median(L[mn]); key = f'{c}_{e_}'; rep['T'][key] = {}
        for a0 in range(0, 360, 30):
            sec = (((P_ - a0) % 360) < 30) & np.isfinite(L); row = {}
            # nivell local del sector a 8–14 px (treu el desnivell de sector, com fa j14)
            ml = sec & (D_ >= 8) & (D_ < 14); lv = float(np.median(L[ml])) if ml.sum() > 300 else 0.0
            for k in range(DB.size - 1):
                m = sec & (D_ >= DB[k]) & (D_ < DB[k + 1])
                if m.sum() >= 150: row[f'{DB[k]:.1f}'] = round(float(np.median(L[m])) - lv, 3)
            if row: rep['T'][key][f'{a0}'] = row
        print(key)
        for a0, row in rep['T'][key].items(): print('  PA', a0, ' '.join(f"{k}:{v:+.2f}" for k, v in row.items() if float(k) in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0)))
(O / 'D19_SILUETA_I_COLLAPSE.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=float))
