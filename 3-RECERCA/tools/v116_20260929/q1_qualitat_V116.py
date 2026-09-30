"""q1 (V116, 29-09-2026) · Qualitat sobre els COMPOSTOS DESATS (renders natius del Photoshop, amb els ajustos de Pere recalculats), NOMÉS amb la nostra dada:
contrast cru de les 11 marques de Pere, terra físic (corona ≥ cel), simetria del realç respecte de la fusió lineal pròpia, canvi de gran escala respecte de
la V115; Brno 200 mm només com a CONTROL (no decideix). Mateixes funcions que e2/e3 (còpia), sobre la lluminància mitjana RGB a 1/4.
Ús: q1_qualitat_V116.py <sortida.json> <nom=render.tif> [...]   (el primer és la referència del canvi de gran escala)"""
import sys, json, numpy as np, cv2, tifffile
from pathlib import Path
from scipy import ndimage as ndi
ARREL = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, q_blocs
O = ARREL / '4-RESULTATS/v116_20260929'
p = PSB(str(ARREL / '1-PHOTOSHOP/V115.psb')); H, W = p.height, p.width
lab = np.load(O / 'marques_V115_etiquetes.npy'); M = json.load(open(O / 'MARQUES_V115.json'))['marques']

def quart(x): return x[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4).mean((1, 3))
RENDERS = {a.split('=')[0]: Path(a.split('=')[1]) for a in sys.argv[2:]}
L4 = {}
for nom, f in RENDERS.items():
    im = tifffile.memmap(f, mode='r'); assert im.shape == (H, W, 3); acc = np.zeros((H // 4, W // 4), np.float32)
    for c in range(3): acc += quart(np.asarray(im[..., c], np.float32) / 65535) / 3
    L4[nom] = acc; print(nom, 'llegit', flush=True)
lab4 = lab[:H // 4 * 4:4, :W // 4 * 4:4]; SOL = (5361.768 / 4, 3775.748 / 4); RS = 440.603 / 4
yy, xx = np.mgrid[0:H // 4, 0:W // 4]; rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS; X = (xx - SOL[0]) / 1000; Y = (yy - SOL[1]) / 1000
dist = {m['marca']: ndi.distance_transform_edt(lab4 != m['marca']) * 4 for m in M}
def contrast(L):
    v4 = L > 0.004; o = {}
    for m in M:
        k = m['marca']; d = (lab4 == k) & v4; f = (dist[k] > 60) & (dist[k] < 300) & (lab4 == 0) & v4
        o[k] = round(float(L[d].mean() / L[f].mean() - 1) * 100, 2) if d.any() and f.any() else None
    return o
def cel(L):
    sel = (L > 0.004) & (rr > 6.5) & (rr < 8.4) & (lab4 == 0)
    A = np.stack([np.ones(sel.sum()), X[sel], Y[sel], X[sel] ** 2 - Y[sel] ** 2, X[sel] * Y[sel]], 1); b = L[sel]; ok = np.ones(len(b), bool)
    for _ in range(4):
        cf, *_ = np.linalg.lstsq(A[ok], b[ok], rcond=None); res = b - A @ cf; s = np.std(res[ok]); ok = np.abs(res) < 2.5 * s
    return cf[0] + cf[1] * X + cf[2] * Y + cf[3] * (X ** 2 - Y ** 2) + cf[4] * X * Y
def terra(L):
    S = cel(L); g = L / np.maximum(S, 1e-6); cor = (L > 0.004) & (rr > 1.3) & (rr < 6)
    o = dict(fraccio_sota_cel=round(float(np.mean(g[cor] < 0.995)), 4), p1=round(float(np.percentile(g[cor], 1)), 3), marques={})
    for m in M:
        k = (lab4 == m['marca']) & (L > 0.004)
        if k.any(): o['marques'][m['marca']] = dict(sota=round(float(np.mean(g[k] < 0.995)), 3), p5=round(float(np.percentile(g[k], 5)), 3))
    return o
# pla polar (com a4)
Rr = np.arange(int(1.15 * RS), int(9.6 * RS)).astype(np.float32); NT = 7200; TH = np.arange(NT) * 2 * np.pi / NT
MX = (SOL[0] + Rr[:, None] * np.cos(TH)[None, :]).astype(np.float32); MY = (SOL[1] - Rr[:, None] * np.sin(TH)[None, :]).astype(np.float32)
LABP = cv2.remap(lab4.astype(np.float32), MX, MY, cv2.INTER_NEAREST, borderValue=0).astype(np.int16); RP = (Rr / RS)[:, None] * np.ones((1, NT), np.float32)
def zloc(L):
    P = cv2.remap(L.astype(np.float32), MX, MY, cv2.INTER_LINEAR, borderValue=0); v = P > 1e-6
    lp = np.where(v, np.log(np.maximum(P, 1e-12)), np.nan); z = lp - np.nanmedian(lp, 1, keepdims=True)
    zz = np.where(v, z, 0); vv = v.astype(np.float32); s = 6 / 360 * NT
    num = ndi.gaussian_filter1d(zz, s, axis=1, mode='wrap'); den = ndi.gaussian_filter1d(vv, s, axis=1, mode='wrap')
    zl = np.where(v & (den > 0.5), z - num / np.maximum(den, 1e-6), np.nan)
    n2 = ndi.gaussian_filter(np.nan_to_num(zl), (2, 1), mode=('nearest', 'wrap')); d2 = ndi.gaussian_filter(np.isfinite(zl).astype(np.float32), (2, 1), mode=('nearest', 'wrap'))
    return np.where(np.isfinite(zl) & (d2 > 0.5), n2 / np.maximum(d2, 1e-6), np.nan).astype(np.float32)
LINp = np.load(ARREL / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/d4/products/sources/fusion_starless.npy', mmap_mode='r')
zl_lin = zloc(np.mean([quart(np.asarray(LINp[..., c], np.float32)) for c in range(3)], 0))
BANDES = ((1.3, 2.0), (2.0, 3.5), (3.5, 5.5), (5.5, 9.5))
def trams(x, y):
    q = np.quantile(x, np.linspace(0.01, 0.99, 50)); xm, ym = [], []
    for lo, hi in zip(q[:-1], q[1:]):
        s = (x >= lo) & (x < hi)
        if s.sum() > 100: xm.append(np.median(x[s])); ym.append(np.median(y[s]))
    xm, ym = np.array(xm), np.array(ym); n_, p_ = xm < 0, xm > 0
    return float(np.sum(xm[n_] * ym[n_]) / np.sum(xm[n_] ** 2)), float(np.sum(xm[p_] * ym[p_]) / np.sum(xm[p_] ** 2))
def simetria(L):
    zo = zloc(L); o = dict(bandes={}, marques={})
    for a, b in BANDES:
        k = (RP >= a) & (RP < b) & (LABP == 0) & np.isfinite(zl_lin) & np.isfinite(zo); gm, gp = trams(zl_lin[k], zo[k])
        o['bandes'][f'{a}-{b}'] = dict(g_fosc=round(gm, 2), g_clar=round(gp, 2), A=round(gm / gp, 2))
    for m in M:
        kk = (LABP == m['marca']) & np.isfinite(zl_lin) & np.isfinite(zo); bn = next((f'{a}-{b}' for a, b in BANDES if a <= m['r_Rsol'] < b), None)
        if kk.sum() < 20 or bn is None: continue
        cl_, co_ = float(np.mean(zl_lin[kk])), float(np.mean(zo[kk])); o['marques'][m['marca']] = dict(z_out=round(co_ * 100, 2), esperat=round(cl_ * o['bandes'][bn]['g_clar'] * 100, 2))
    return o
def gran(L):
    v = L > 0.004; return ndi.gaussian_filter(np.where(v, L, 0), 75) / np.maximum(ndi.gaussian_filter(v.astype(np.float32), 75), 1e-6), v
G0, V0 = gran(L4[list(RENDERS)[0]]); res = {}
for k, L in L4.items():
    Gk, _ = gran(L); dom = V0 & (rr > 1.2); r_ = (Gk[dom] / np.maximum(G0[dom], 1e-6) - 1) * 100
    res[k] = dict(contrast=contrast(L), terra=terra(L), simetria=simetria(L), canvi_gran_escala=[round(float(np.percentile(r_, q)), 2) for q in (1, 50, 99)])
res['control Brno 200 (no és criteri)'] = dict(contrast=contrast(np.load(ARREL / '4-RESULTATS/v114_artefactes_foscos_20260929/estadis_1a4/brno_230_L.npy')))
json.dump(dict(nota=__doc__.split('\n')[0], renders={k: str(v) for k, v in RENDERS.items()}, resultats=res), open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
print('contrast cru (%)'.ljust(34), ' '.join(f'{m["marca"]:>6d}' for m in M))
for k, r in res.items(): print(k[:34].ljust(34), ' '.join(f"{(r['contrast'][m['marca']] or 0):6.2f}" for m in M))
for k, r in res.items():
    if 'terra' not in r: continue
    print(f"{k[:20]:20s} sota el cel {r['terra']['fraccio_sota_cel'] * 100:5.2f} % (p1 {r['terra']['p1']}) · marques sota:", ' '.join(f"{i}:{v['sota']:.2f}" for i, v in r['terra']['marques'].items()))
    print(' ' * 21, 'simetria A per bandes', {b: v['A'] for b, v in r['simetria']['bandes'].items()}, '· canvi gran escala', r['canvi_gran_escala'])
    print(' ' * 21, 'marques z_out/esperat', ' '.join(f"{i}:{v['z_out']:.1f}/{v['esperat']:.1f}" for i, v in r['simetria']['marques'].items()))
