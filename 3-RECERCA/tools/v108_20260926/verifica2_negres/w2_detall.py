"""w2 (V108 · verifica2_negres) · Detall a pas 1 dins del marc, amb compositor propi (w0): energia per escales i bandes (DoG de ln L),
flamarada (p90 − p10 del pas alt tangencial 3–128 px d'arc als anells), jutge Brno (correlació del pas alt tangencial 2–64 px d'arc de ln L
amb els composts de Brno 230–233), perles del limbe (DoG 1–4 a 1,02–1,15 R☉), soroll del cel (DoG 0–1 i 1–2 a > 7 R☉) i canvi absolut
del compost per sectors de 45° a 3–4,5 R☉. Ús: w2_detall.py [carpeta_candidat]"""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
sys.path.insert(0, str(Path(__file__).resolve().parent))
from w0_comu import *
T0 = time.time()
CAND = Path(sys.argv[1]) if len(sys.argv) > 1 else R0 / '4-RESULTATS/v108_20260926/negres_v2/candidats_v4/CEL_G_MAX_T_e30_W_H0'
NOM = CAND.name; BOX = MARC
G = geo(BOX, 1); r, th, ok = G['r'], G['th'], G['ok']; del G
mg = np.zeros_like(ok); mg[80:-80, 80:-80] = True; ok &= mg
L0 = compon(BOX, 1); L1 = compon(BOX, 1, cand=CAND); print('composts', round(time.time() - T0), 's', flush=True)
l0 = np.log(np.maximum(L0, 1e-3)); l1 = np.log(np.maximum(L1, 1e-3)); res = dict(candidat=str(CAND))
def dog(a, s1, s2): return (a if s1 == 0 else cv2.GaussianBlur(a, (0, 0), s1)) - cv2.GaussianBlur(a, (0, 0), s2)
BANDES = ((1.02, 1.3), (1.3, 2), (2, 3), (3, 4.5), (4.5, 7), (7, 9.5))
en = {}
for esc, (s1, s2) in {'1-2': (1, 2), '2-8': (2, 8), '8-32': (8, 32), '32-128': (32, 128)}.items():
    d0 = dog(l0, s1, s2); d1 = dog(l1, s1, s2)
    for a, b in BANDES:
        m = ok & (r >= a) & (r < b)
        if m.sum() < 1000: continue
        en.setdefault(esc, {})[f'{a:g}-{b:g}'] = float(np.sqrt(np.mean(d1[m] ** 2) / np.mean(d0[m] ** 2)))
        if esc == '2-8' and (a, b) in ((2, 3), (3, 4.5)):   # ordre clar/fosc
            x, y = d0[m], d1[m]; en.setdefault('corr_2-8', {})[f'{a:g}-{b:g}'] = float(np.corrcoef(x, y)[0, 1])
    del d0, d1
res['energia_quocient'] = en
d0 = dog(l0, 0, 1); d1 = dog(l1, 0, 1); m = ok & (r >= 7)
res['soroll_cel_0-1_quocient'] = float(np.sqrt(np.mean(d1[m] ** 2) / np.mean(d0[m] ** 2)))
m = ok & (r >= 1.02) & (r < 1.15); d0 = dog(l0, 1, 4); d1 = dog(l1, 1, 4)
res['perles_1.02-1.15_quocient_rms_dog14'] = float(np.sqrt(np.mean(d1[m] ** 2) / np.mean(d0[m] ** 2))); res['perles_px_iguals'] = float((L0[m] == L1[m]).mean()); del d0, d1
# canvi absolut del compost per sectors de 45° (3–4,5 R☉)
dl = l1 - l0; res['canvi_lnL_3-4.5_per_sectors45_p50'] = [float(np.median(dl[ok & (r >= 3) & (r < 4.5) & (th >= s) & (th < s + 45)])) for s in range(0, 360, 45)]
res['canvi_lnL_2-3_per_sectors45_p50'] = [float(np.median(dl[ok & (r >= 2) & (r < 3) & (th >= s) & (th < s + 45)])) for s in range(0, 360, 45)]
del dl
# anells polars al voltant del Sol (coordenades del marc)
x0, y0 = BOX[0], BOX[1]; okf = ok.astype(np.float32)
def anell(img, rs, dr=6, pasr=2.0):
    n = int(2 * np.pi * rs * RSOL); t = np.linspace(0, 2 * np.pi, n, endpoint=False, dtype=np.float32)
    rr = np.arange(rs * RSOL - dr, rs * RSOL + dr + 0.1, pasr, dtype=np.float32)
    X = (SOL[0] - x0 + np.cos(t)[None, :] * rr[:, None]).astype(np.float32); Y = (SOL[1] - y0 - np.sin(t)[None, :] * rr[:, None]).astype(np.float32)
    v = cv2.remap(okf, X, Y, cv2.INTER_LINEAR).min(0) > 0.999
    return cv2.remap(np.ascontiguousarray(img, np.float32), X, Y, cv2.INTER_LINEAR).mean(0), v
def pasalt(lp, v, s1, s2):
    w = v.astype(np.float64); a = gaussian_filter1d(lp * w, s1, mode='wrap') / np.maximum(gaussian_filter1d(w, s1, mode='wrap'), 1e-6)
    W2 = gaussian_filter1d(w, s2, mode='wrap'); b = gaussian_filter1d(lp * w, s2, mode='wrap') / np.maximum(W2, 1e-6); return a - b, v & (W2 > 0.5)
fl = {}
for rs in (1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.5):
    p0, v = anell(L0, rs); p1, _ = anell(L1, rs)
    h0, vv = pasalt(np.log(np.maximum(p0, 1e-3)), v, 3, 128); h1, _ = pasalt(np.log(np.maximum(p1, 1e-3)), v, 3, 128)
    fl[f'{rs:g}'] = float((np.percentile(h1[vv], 90) - np.percentile(h1[vv], 10)) / (np.percentile(h0[vv], 90) - np.percentile(h0[vv], 10)))
res['flamarada_quocient'] = fl
BR = R0 / '4-RESULTATS/v108_20260926/negres/pas1'; br = {}
for lid in (230, 231, 232, 233):
    Bn = np.load(BR / f'Brno_{lid}.npy'); assert Bn.shape == L0.shape
    for a, b in ((1.3, 2), (2, 3), (3, 4.5)):
        xs0, xs1, ys = [], [], []
        for rs in np.arange(a + 0.05, b, 0.1):
            q, v = anell(Bn, rs, dr=4); p0, _ = anell(L0, rs, dr=4); p1, _ = anell(L1, rs, dr=4); v &= q > 1e-3
            if v.sum() < 500: continue
            hb, vv = pasalt(np.log(np.maximum(q, 1e-3)), v, 2, 64); h0, _ = pasalt(np.log(np.maximum(p0, 1e-3)), v, 2, 64); h1, _ = pasalt(np.log(np.maximum(p1, 1e-3)), v, 2, 64)
            ys.append(hb[vv]); xs0.append(h0[vv]); xs1.append(h1[vv])
        if ys:
            ys = np.concatenate(ys); xs0 = np.concatenate(xs0); xs1 = np.concatenate(xs1)
            br.setdefault(str(lid), {})[f'{a:g}-{b:g}'] = [float(np.corrcoef(xs0, ys)[0, 1]), float(np.corrcoef(xs1, ys)[0, 1])]
    del Bn
res['brno_V107_cand'] = br
res['segons'] = round(time.time() - T0)
(OUT / f'W2_{NOM}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n'); print('FET', res['segons'], 's')
