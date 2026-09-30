"""y5 (verificador adversari 4; còpia del x5 del verificador 3 amb la v4 i una altra llavor) · Els sis traços T1–T6 amb GEOMETRIA FIXA (centre, direcció i llarg de C5_PERFILS de la V93, solc centrat a
V0_minim_t, sense cap cerca) i NULS A LA MATEIXA IMATGE: 300 segments a l'atzar (llavor 777, diferent de la de l'autor i de la del verificador 2),
del mateix llarg, a ±35 % de la distància al Sol, angle a l'atzar, cobertura ≥ 90 %.
Detall: DoG del ln σ3 − σ30. Solc = mitjana |t| ≤ 6 px − mitjana 20 ≤ |t| ≤ 80 px (‱). Per a control, v2 i v3; z i p contra els nuls; i el canvi
(v − control) del traç contra el canvi dels mateixos nuls (z_canvi).
També T1..T6 a ln A − ln B (Sony) per a control, v2, v3: el que va fix al sensor.
Ús: y5_tracos.py [compost base vixen sonyA sonyB AB]   Sortida: 4-RESULTATS/v108_20260926/verifica4_flat2d/Y5_TRACOS.json"""
import json, sys
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica4_flat2d'
W, H = 10551, 7506; SOL = np.array([5361.768, 3775.748])
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'; F4 = A / '4-RESULTATS/v108_20260926/flat2d_v4'; CAD = A / '4-RESULTATS/v108_20260926/cadena'; CR = A / '4-RESULTATS/v97_refundacio_20260924'
IM = {'compost': ({'control': F2 / 'compost_control.npy', 'v2': F2 / 'compost_flat2d_v2.npy', 'v3': F3 / 'compost_flat2d_v3.npy', 'v4': F4 / 'compost_flat2d_v4.npy'}, None),
      'base': ({'control': CAD / 'control/lineal/base_G.npy', 'v2': CAD / 'flat2d_v2/lineal/base_G.npy', 'v3': CAD / 'flat2d_v3/lineal/base_G.npy'}, None),
      'vixen': ({'control': CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', 'v2': F2 / 'apilats/vixen_total.npy', 'v3': F3 / 'apilats/vixen_total.npy'}, 1),
      'sonyA': ({'control': CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', 'v2': F2 / 'apilats/sony_A_total.npy', 'v3': F3 / 'apilats/sony_A_total.npy', 'v4': F4 / 'apilats/sony_A_total.npy'}, 1),
      'sonyB': ({'control': CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy', 'v2': F2 / 'apilats/cau/sony_B_total_v42.npy', 'v3': F3 / 'apilats/cau/sony_B_total_v42.npy', 'v4': F4 / 'apilats/cau/sony_B_total_v42.npy'}, 1)}
quins = sys.argv[1:] or ['compost', 'base', 'vixen', 'sonyA', 'sonyB', 'AB']
C5 = json.loads((A / '4-RESULTATS/v93_20260924/C5_PERFILS.json').read_text())['tracos']
TR = []
for k, t in enumerate(C5):
    d = np.array(t['info']['direccio'], float); d /= np.linalg.norm(d)
    TR.append((k + 1, np.array(t['info']['centre'], float) + float(t['info']['V0_minim_t']) * np.array([-d[1], d[0]]), d, float(t['info']['llarg'])))
TT = np.arange(-80, 81, 1.0); CORE = np.abs(TT) <= 6; FLANC = (np.abs(TT) >= 20) & (np.abs(TT) <= 80)
def lnm(p, ch):
    a = np.load(p, mmap_mode='r'); img = np.asarray(a if ch is None else a[..., ch], np.float32)
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32), m
def dog(l, m):
    g = lambda s: cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
    return np.where(cv2.erode(m, np.ones((61, 61), np.uint8)) > 0, g(3) - g(30), np.nan).astype(np.float32)
def solc(D, c, d, L):
    n = np.array([-d[1], d[0]]); s = np.arange(-L / 2, L / 2 + 1e-6, 2.0)
    X = (c[0] + s[:, None] * d[0] + TT[None, :] * n[0]).astype(np.float32); Y = (c[1] + s[:, None] * d[1] + TT[None, :] * n[1]).astype(np.float32)
    P = cv2.remap(D, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
    if np.isfinite(P[:, CORE | FLANC]).all(1).mean() < 0.9: return np.nan
    with np.errstate(all='ignore'): pr = np.nanmean(P, 0)
    return float(1e4 * (np.nanmean(pr[CORE]) - np.nanmean(pr[FLANC])))
rng = np.random.default_rng(20260927); NUL = {}
for k, c0, d0, L in TR:
    rs = np.linalg.norm(c0 - SOL); A_ = []
    while len(A_) < 300:
        ang = rng.uniform(0, 2 * np.pi); rr = rs * rng.uniform(0.65, 1.35); c = SOL + rr * np.array([np.cos(ang), np.sin(ang)])
        th = rng.uniform(0, np.pi); d = np.array([np.cos(th), np.sin(th)]); e1, e2 = c + d * L / 2, c - d * L / 2
        if min(e1[0], e2[0]) > 150 and min(e1[1], e2[1]) > 150 and max(e1[0], e2[0]) < W - 150 and max(e1[1], e2[1]) < H - 150: A_.append((c, d))
    NUL[k] = A_
fp = OUT / 'Y5_TRACOS.json'; R = json.loads(fp.read_text()) if fp.exists() else {}
def avalua(Dfun):
    vals = {}
    for v in ('control', 'v3', 'v4'):
        D = Dfun(v); vals[v] = {k: (solc(D, c0, d0, L), np.array([solc(D, c, d, L) for c, d in NUL[k]])) for k, c0, d0, L in TR}; del D
    res = {}
    for k, c0, d0, L in TR:
        o = {}
        for v in vals:
            t, nn = vals[v][k]; ok = np.isfinite(nn)
            if not np.isfinite(t) or ok.sum() < 30: o[v] = None; continue
            o[v] = dict(solc=round(t, 2), z=round(float((t - nn[ok].mean()) / nn[ok].std()), 2), p=round(float(((nn[ok] <= t).sum() + 1) / (ok.sum() + 1)), 4), sd_nul=round(float(nn[ok].std()), 2))
        for v in ('v3', 'v4'):
            if o.get(v) and o.get('control'):
                dn = vals[v][k][1] - vals['control'][k][1]; ok = np.isfinite(dn); dt = vals[v][k][0] - vals['control'][k][0]
                o[f'canvi_{v}'] = round(dt, 2); o[f'z_canvi_{v}'] = round(float((dt - dn[ok].mean()) / dn[ok].std()), 2)
        res[f'T{k}'] = o
    return res
for nom in quins:
    if nom == 'AB':
        def Dfun(v):
            la, ma = lnm(IM['sonyA'][0][v], 1); lb, mb = lnm(IM['sonyB'][0][v], 1); m = ma * mb
            return dog(np.where(m > 0, la - lb, 0).astype(np.float32), m)
    else:
        ps, ch = IM[nom]
        def Dfun(v, ps=ps, ch=ch):
            l, m = lnm(ps[v], ch); return dog(l, m)
    R[nom] = avalua(Dfun); print(nom, json.dumps(R[nom]), flush=True); fp.write_text(json.dumps(R, ensure_ascii=False, indent=1))
