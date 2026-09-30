"""n3 (V108 · negres) · (4) Avaluació de les cures emulant la pila de la V107 (modes, opacitats i màscares de la V107; sense capes d'ajust):
el ràster candidat substitueix el de la 41 i la 42 (i, si n'hi ha, el de la 56). Mètriques:
  · zones negres (n1.zones: global, local, local suau σ 6 px; per bandes i sectors) i cel (màx/mín entre sectors) — llenç sencer, pas 2;
  · energia del detall: rms de la DoG de ln L a 1–2, 2–8, 8–32 px (pas 1, dins del marc) i 32–128 px (pas 2), per bandes;
  · ordre clar/fosc: pendent de la DoG 2–32 de la candidata contra la de la V107, separat per signe, i correlació;
  · contrast plomall/buit («flamarada»): p90 − p10 del detall tangencial de ln L (σ 3 px d'arc menys σ 128) als anells 1,5…4,5 R☉;
  · perles del limbe (1,02–1,15 R☉): p99,5 i rms de la DoG 1–4; protuberància esquerra;
  · soroll del cel: rms de la DoG 0–1 i 1–2 a > 7 R☉ i a 4,5–7 R☉;
  · jutge Brno: correlació del detall tangencial 2–64 px d'arc amb els composts 230–233 (cap píxel de Brno entra enlloc), per bandes.
Ús: n3_avalua.py <nom>=<carpeta de candidat o 'V107'>[,<lid56>=<npy>] …   (resultats a N3_<nom>.json; L a pas2/ i pas1/)"""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_negres import *
from n1_mesura_v107 import zones, r as r2, th as th2, ok as ok2, okm as okm2
d1 = OUT / 'pas1'; d1.mkdir(exist_ok=True); d2 = OUT / 'pas2'
CAND = OUT / 'candidats'


def esp_de(spec):
    """'V107' o 'CARPETA[+56=RUTA][+54=RUTA]' → variant per a Pila."""
    parts = spec.split('+'); esp = {}
    if parts[0] != 'V107':
        c = Path(parts[0]); c = c if c.is_absolute() else CAND / c
        esp[41] = {'F': str(c / 'P01_NRGF_u16.npy')}; esp[42] = {'F': str(c / 'P01_NRGF_extrap_u16.npy')}
    for p in parts[1:]:
        lid, ruta = p.split('='); esp[int(lid)] = {'F': ruta}
    return esp


# ---------- geometria pas 1 (marc) ----------
BOX1 = MARC
G1 = mascares(BOX1, 1); r1, th1, ok1 = G1['r'], G1['th'], G1['ok']; mg = np.zeros_like(ok1); mg[100:-100, 100:-100] = True; okk = ok1 & mg
x0, y0 = MARC[0], MARC[1]
RINGS = []
for b in BANDES:
    hi = min(b[1], 9.2)
    for a in np.arange(b[0], hi - 1e-6, 0.1):
        rr = np.arange(a * RSOL, min(a + 0.1, hi) * RSOL, 4.0, dtype=np.float32)
        if len(rr) == 0: continue
        nth = int(round(2 * np.pi * (a + 0.05) * RSOL)); t = np.linspace(0, 2 * np.pi, nth, endpoint=False, dtype=np.float32)
        RINGS.append((NB(b), (SOL[0] - x0 + np.cos(t)[None, :] * rr[:, None]).astype(np.float32), (SOL[1] - y0 - np.sin(t)[None, :] * rr[:, None]).astype(np.float32)))
def pol(a, X, Y): return cv2.remap(np.ascontiguousarray(a, np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)
okf = ok1.astype(np.float32); WR = [pol(okf, X, Y) > 0.999 for _, X, Y in RINGS]
def hp(l, wv, s1=2.0, s2=64.0):
    ww = wv.astype(np.float32); lw = l * ww
    g1 = gaussian_filter1d(lw, s1, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(ww, s1, axis=1, mode='wrap'), 1e-6)
    W2 = gaussian_filter1d(ww, s2, axis=1, mode='wrap'); g2 = gaussian_filter1d(lw, s2, axis=1, mode='wrap') / np.maximum(W2, 1e-6)
    return g1 - g2, wv & (W2 > 0.5)
def brno():
    out = {}
    for lid in (230, 231, 232, 233):
        p = d1 / f'Brno_{lid}.npy'
        if not p.exists():
            B = E5.rgb(lid, BOX1); np.save(p, (lum(B) if B.ndim == 3 else B).astype(np.float32)); del B
        B = np.ascontiguousarray(np.load(p, mmap_mode='r')); out[lid] = []
        for (nb, X, Y), wv in zip(RINGS, WR):
            q = pol(B, X, Y); out[lid].append(hp(np.log(np.maximum(q, 1e-3)), wv & (q > 1e-3)))
        del B
    return out


def metriques_pas1(L, Lref=None):
    l = logL(L); R = {}
    SC = {'0-1': (0, 1), '1-2': (1, 2), '2-8': (2, 8), '8-32': (8, 32)}
    D = {k: dog(l, *s) for k, s in SC.items()}
    for b in BANDES:
        m = okk & (r1 >= b[0]) & (r1 < b[1]); R[NB(b)] = {f'rms_{k}': float(np.sqrt(np.mean(D[k][m] ** 2))) for k in SC}; R[NB(b)]['mediana_L'] = float(np.median(L[m]))
    R['soroll'] = {z: {k: float(np.sqrt(np.mean(D[k][m] ** 2))) for k in ('0-1', '1-2')} for z, m in {'cel_>7': okk & (r1 >= 7), 'corona_feble_4.5-7': okk & (r1 >= 4.5) & (r1 < 7)}.items()}
    del D
    d232 = dog(l, 2, 32)
    if Lref is not None:
        dr = dog(logL(Lref), 2, 32); R['ordre'] = {}
        for b in BANDES[1:5]:
            m = okk & (r1 >= b[0]) & (r1 < b[1]); x = dr[m]; y = d232[m]; pos = x > 0; neg = x < 0
            R['ordre'][NB(b)] = dict(corr=float(np.corrcoef(x, y)[0, 1]), pendent_clars=float((x[pos] * y[pos]).sum() / (x[pos] ** 2).sum()),
                                     pendent_foscos=float((x[neg] * y[neg]).sum() / (x[neg] ** 2).sum()), signe_invertit=float(((x * y) < 0)[np.abs(x) > np.std(x)].mean()))
        del dr
    del d232
    # perles i protuberància esquerra
    d14 = dog(l, 1, 4); m = okk & (r1 >= 1.02) & (r1 < 1.15)
    R['perles_1.02-1.15'] = dict(p99_5_dog_1_4=float(np.percentile(d14[m], 99.5)), rms_dog_1_4=float(np.sqrt(np.mean(d14[m] ** 2))), frac_dog_1_4_sobre_0_05=float((d14[m] > 0.05).mean()))
    del d14
    # flamarada: detall tangencial p90 − p10 i contrast de zona
    fl = {}
    for rs in (1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5):
        n = int(2 * np.pi * rs * RSOL); t = np.linspace(0, 2 * np.pi, n, endpoint=False, dtype=np.float32)
        rr = np.arange(rs * RSOL - 6, rs * RSOL + 6.1, 2.0, dtype=np.float32)
        X = (SOL[0] - x0 + np.cos(t)[None, :] * rr[:, None]).astype(np.float32); Y = (SOL[1] - y0 - np.sin(t)[None, :] * rr[:, None]).astype(np.float32)
        v = pol(okf, X, Y).min(0) > 0.999; p = pol(L, X, Y).mean(0)
        lp = np.log(np.maximum(p, 1e-3)); ww = v.astype(np.float64)
        s3 = gaussian_filter1d(lp * ww, 3.0, mode='wrap') / np.maximum(gaussian_filter1d(ww, 3.0, mode='wrap'), 1e-6)
        s128 = gaussian_filter1d(lp * ww, 128.0, mode='wrap') / np.maximum(gaussian_filter1d(ww, 128.0, mode='wrap'), 1e-6)
        hpp = (s3 - s128)[v]; fl[f'{rs:g}'] = dict(p90_menys_p10_ln=float(np.percentile(hpp, 90) - np.percentile(hpp, 10)), p10_ln=float(np.percentile(hpp, 10)), p90_ln=float(np.percentile(hpp, 90)))
    R['flamarada'] = fl
    # Brno
    pols = []
    for (nb, X, Y), wv in zip(RINGS, WR):
        q = pol(L, X, Y); pols.append(hp(np.log(np.maximum(q, 1e-3)), wv & (q > 1e-3)))
    fb = {}; tang = {}
    for nb in [NB(b) for b in BANDES]:
        ii = [i for i, rg in enumerate(RINGS) if rg[0] == nb]
        tang[nb] = float(np.sqrt(np.mean(np.concatenate([pols[i][0][pols[i][1]] for i in ii]) ** 2)))
        for lid in BR:
            xs, ys = [], []
            for i in ii:
                mm = pols[i][1] & BR[lid][i][1]; xs.append(pols[i][0][mm]); ys.append(BR[lid][i][0][mm])
            xs = np.concatenate(xs); ys = np.concatenate(ys)
            if len(xs) > 5000: fb.setdefault(str(lid), {})[nb] = float(np.corrcoef(xs, ys)[0, 1])
    R['tangencial_rms_2-64'] = tang; R['brno_corr_tangencial_2-64'] = fb
    return R


def metriques_pas2(L):
    z, sky, skys, Ls = zones(L); l = logL(L); dd = dog(l, 16, 64)   # 32–128 px del llenç
    for b in BANDES:
        m = okm2 & (r2 >= b[0]) & (r2 < b[1]); z.setdefault('rms_32-128', {})[NB(b)] = float(np.sqrt(np.mean(dd[m] ** 2)))
    return z, sky, skys, Ls


if __name__ == '__main__':
    BR = brno(); print('Brno llest', flush=True)
    P2 = Pila((0, 0, W, H), 2); P1 = Pila(BOX1, 1); print('piles llestes', flush=True)
    Lref1 = None; pref = d1 / 'L_V107.npy'
    if pref.exists(): Lref1 = np.load(pref)
    for arg in sys.argv[1:]:
        nom, spec = arg.split('=', 1) if '=' in arg.split('+')[0] else (arg, arg)
        t = time.time(); res = dict(spec=spec)
        L2 = P2.compon(esp_de(spec)); np.save(d2 / f'L_{nom}.npy', L2); res['pas2'], *_ = metriques_pas2(L2); del L2
        L1 = P1.compon(esp_de(spec)); np.save(d1 / f'L_{nom}.npy', L1)
        if nom == 'V107': Lref1 = L1
        res['pas1'] = metriques_pas1(L1, None if nom == 'V107' else Lref1); del L1
        desa(OUT / f'N3_{nom}.json', res)
        z = res['pas2']['1.3-4.5']; f = res['pas1']['flamarada']; bz = res['pas1']['brno_corr_tangencial_2-64']
        print(nom, round(time.time() - t), 's · negres local', round(z['local'], 4), 'suau', round(z['local_suau'], 4), 'global', round(z['global_'], 4),
              '· cel màx/mín', round(res['pas2']['cel_max_sobre_min'], 3), '· flam 1.5/3/4', round(f['1.5']['p90_menys_p10_ln'], 3), round(f['3']['p90_menys_p10_ln'], 3), round(f['4']['p90_menys_p10_ln'], 3),
              '· Brno230 2-3/3-4.5', bz.get('230', {}).get('2-3'), bz.get('230', {}).get('3-4.5'), flush=True)
