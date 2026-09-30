"""w2c (verificador adversari 2) · com w2, però amb el solc centrat a t0 = V0_minim_t de C5 (mesurat a la V92, dada independent) i DoG σ3−σ30.
w2 · Els sis traços, amb una MESURA PRÒPIA i GEOMETRIA FIXA (sense cercar angle ni posició), abans i després.
Detall: DoG del ln, σ2 − σ20 (normalitzat amb la màscara de dada). Perfil perpendicular mitjà al llarg de tot el traç (geometria de la marca 269,
C5_PERFILS). Solc = mitjana a |t| ≤ 8 px − mitjana a 20 ≤ |t| ≤ 80 px. Nuls, mesurats A CADA IMATGE i a les mateixes posicions:
  P · 28 rectes paral·leles desplaçades ±100…±1.400 px;  A · 300 segments a l'atzar (llavor 4242) del mateix llarg, a una distància del Sol
  dins de ±35 % de la del traç, amb angle a l'atzar, cobertura ≥ 90 %.
Per a cada traç: solc (‱), z contra A, p = (n nuls ≤ valor + 1)/(n + 1); i el CANVI (després − abans) del traç contra el canvi dels mateixos nuls
(z_canvi): diu si la cura actua sobre el traç més que sobre un segment qualsevol.
Ús: w2_tracos.py   Sortida: 4-RESULTATS/v108_20260926/verifica2_marrons/W2_TRACOS.json"""
import json, sys
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica2_marrons'
W, H = 10551, 7506; SOL = np.array([5361.768, 3775.748])
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; CAD = A / '4-RESULTATS/v108_20260926/cadena'; CR = A / '4-RESULTATS/v97_refundacio_20260924'
PARELLS = {
    'compost': (F2 / 'compost_control.npy', F2 / 'compost_flat2d_v2.npy', None),
    'base_G': (CAD / 'control/lineal/base_G.npy', CAD / 'flat2d_v2/lineal/base_G.npy', None),
    'vixen_G': (CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', F2 / 'apilats/vixen_total.npy', 1),
    'sonyA_G': (CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', F2 / 'apilats/sony_A_total.npy', 1),
    'sonyB_G': (CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy', F2 / 'apilats/cau/sony_B_total_v42.npy', 1),
}
quins = sys.argv[1:] or list(PARELLS)
C5 = json.loads((A / '4-RESULTATS/v93_20260924/C5_PERFILS.json').read_text())['tracos']
TR = []
for k, t in enumerate(C5):
    d = np.array(t['info']['direccio'], float); d /= np.linalg.norm(d); TR.append((k + 1, np.array(t['info']['centre'], float) + float(t['info']['V0_minim_t']) * np.array([-d[1], d[0]]), d, float(t['info']['llarg'])))
TT = np.arange(-80, 81, 1.0); CORE = np.abs(TT) <= 6; FLANC = (np.abs(TT) >= 20) & (np.abs(TT) <= 80)
def detall(p, ch):
    a = np.load(p, mmap_mode='r'); img = np.asarray(a if ch is None else a[..., ch], np.float32)
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); l = np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32); del img
    g = lambda s: cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
    ok = cv2.erode(m, np.ones((61, 61), np.uint8)) > 0
    return np.where(ok, g(3) - g(30), np.nan).astype(np.float32)
def solc(D, c, d, L):
    n = np.array([-d[1], d[0]]); s = np.arange(-L / 2, L / 2 + 1e-6, 2.0)
    X = (c[0] + s[:, None] * d[0] + TT[None, :] * n[0]).astype(np.float32); Y = (c[1] + s[:, None] * d[1] + TT[None, :] * n[1]).astype(np.float32)
    P = cv2.remap(D, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
    cov = np.isfinite(P[:, CORE | FLANC]).all(1).mean()
    if cov < 0.9: return np.nan
    with np.errstate(all='ignore'): pr = np.nanmean(P, 0)
    return float(1e4 * (np.nanmean(pr[CORE]) - np.nanmean(pr[FLANC])))
rng = np.random.default_rng(4242); NUL = {}
for k, c0, d0, L in TR:
    n0 = np.array([-d0[1], d0[0]]); rs = np.linalg.norm(c0 - SOL)
    P_ = [(c0 + n0 * sh, d0) for sh in list(range(100, 1401, 100)) + list(range(-100, -1401, -100))]
    A_ = []
    while len(A_) < 300:
        ang = rng.uniform(0, 2 * np.pi); rr = rs * rng.uniform(0.65, 1.35); c = SOL + rr * np.array([np.cos(ang), np.sin(ang)])
        th = rng.uniform(0, np.pi); d = np.array([np.cos(th), np.sin(th)])
        e1, e2 = c + d * L / 2, c - d * L / 2
        if min(e1[0], e2[0]) > 150 and min(e1[1], e2[1]) > 150 and max(e1[0], e2[0]) < W - 150 and max(e1[1], e2[1]) < H - 150: A_.append((c, d))
    NUL[k] = dict(P=P_, A=A_)
R = {}
fp = OUT / 'W2C_TRACOS_T0.json'
if fp.exists(): R = json.loads(fp.read_text())
for nom in quins:
    pa, pd, ch = PARELLS[nom]; res = {}
    vals = {}
    for et, p in (('abans', pa), ('despres', pd)):
        D = detall(p, ch); v = {}
        for k, c0, d0, L in TR:
            v[k] = dict(t=solc(D, c0, d0, L), P=[solc(D, c, d, L) for c, d in NUL[k]['P']], A=[solc(D, c, d, L) for c, d in NUL[k]['A']])
        vals[et] = v; del D
    for k, c0, d0, L in TR:
        o = {}
        for et in ('abans', 'despres'):
            v = vals[et][k]; An = np.array(v['A'], float); Pn = np.array(v['P'], float); ok = np.isfinite(An); okp = np.isfinite(Pn)
            if not np.isfinite(v['t']) or ok.sum() < 30: o[et] = None; continue
            o[et] = dict(solc_ppm=round(v['t'], 2), z_atzar=round(float((v['t'] - An[ok].mean()) / An[ok].std()), 2), p_atzar=round(float(((An[ok] <= v['t']).sum() + 1) / (ok.sum() + 1)), 4),
                         z_paral=(round(float((v['t'] - Pn[okp].mean()) / Pn[okp].std()), 2) if okp.sum() >= 8 else None), n_atzar=int(ok.sum()), sd_atzar_ppm=round(float(An[ok].std()), 2))
        if o['abans'] and o['despres']:
            da = np.array(vals['despres'][k]['A'], float) - np.array(vals['abans'][k]['A'], float); ok = np.isfinite(da); dt = vals['despres'][k]['t'] - vals['abans'][k]['t']
            o['canvi_ppm'] = round(dt, 2); o['z_canvi_contra_atzar'] = round(float((dt - da[ok].mean()) / da[ok].std()), 2); o['canvi_atzar_mitja_sd_ppm'] = [round(float(da[ok].mean()), 2), round(float(da[ok].std()), 2)]
        res[f'T{k}'] = o
    R[nom] = res; print(nom, json.dumps(res), flush=True)
    fp.write_text(json.dumps(R, ensure_ascii=False, indent=1))
