"""e6 (V119): còpia de v118/e5 que admet VÀRIES capes noves damunt de la 56, en ordre: @416:<op>@417:<op> (416 = l'ORDIT de la V119, b8b;
417 = la TRAMA, b9); @415 i @416v118 per a les de la V117 i la V118. e5 (V118): còpia de v117/e4 que admet DUES capes noves possibles damunt de la 56: @415:<op> (la 415 de la V117, filtre A·B) o @416:<op> (la capa nova de la V118, filtre de tres testimonis sense estrelles, 4-RESULTATS/v118_20260929/ABV/capa416). e4 (V117): còpia de v116/e3_avalua_v116.py amb la capa 415 del filtre CORREGIT (4-RESULTATS/v117_20260929/AB/capa415). e3 (V116): còpia de e2 que, a més, pot INSERIR la capa nova 415 (Superposar) just damunt de la 56 amb una opacitat: nom=carpeta[+…]@415:<opacitat 0–1>.
e2 (V116, 29-09-2026) · Avaluació d'una variant sobre la pila de la V115 DE PERE (sota els seus ajustos), amb criteris NOMÉS de la nostra dada:
  (a) contrast cru de les 11 marques de Pere (marca / anell 60–300 px − 1, %);
  (b) TERRA FÍSIC: la corona afegeix llum al cel, així que cap píxel de corona (1,3–6 R☉) no pot quedar sota el cel. Cel = polinomi harmònic de
      2n grau ajustat a 6,5–8,4 R☉ de la MATEIXA imatge; fracció de píxels sota el cel·(1 − 0,5 %) i p1 del quocient;
  (c) SIMETRIA del realç a l'estructura azimutal (pla polar, com a4): g−/g+ per bandes i E per marca respecte de la fusió LINEAL (fonts_c);
  (d) canvi de gran escala respecte de la V115 (σ 300 px; p1, mediana, p99);
  (e) CONTROL (no criteri): el contrast de les marques a Brno 200 mm.
Ús: e2_avalua_v116.py <sortida.json> <nom=carpeta[+carpeta…]> [...]   (cada carpeta aporta les capes de les quals porti el ràster:
    P01_NRGF(_extrap), P02c/P02d_RHEF, 03, 07, 04, P04_WOW, P05_WOW_bilateral; els de 47–56 poden ser també L{id}_G.npy)"""
import sys, json, numpy as np, cv2, tifffile
from pathlib import Path
from scipy import ndimage as ndi
ARREL = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, q_blocs
O = ARREL / '4-RESULTATS/v116_20260929'
p = PSB(str(ARREL / '1-PHOTOSHOP/V115.psb')); H, W = p.height, p.width
lab = np.load(O / 'marques_V115_etiquetes.npy'); M = json.load(open(O / 'MARQUES_V115.json'))['marques']
PILA = [l for l in p.layers if l['visible'] and l['right'] > l['left'] and l['i'] < p.layer(239)['i'] and l['id'] != 414]
NOVA = {}
for a in sys.argv[2:]:
    parts = a.split('=')[1].split('@')[1:]
    if parts: NOVA[a.split('=')[0]] = [(p_.split(':')[0], float(p_.split(':')[1])) for p_ in parts]
VARS = {a.split('=')[0]: [Path(x) for x in a.split('=')[1].split('@')[0].split('+')] for a in sys.argv[2:]}
RAS_NOU = {'415': ARREL / '4-RESULTATS/v117_20260929/AB/capa415/L415_G.npy', '416v118': ARREL / '4-RESULTATS/v118_20260929/ABV/capa416/L415_G.npy',
           '416': ARREL / '4-RESULTATS/v119_20260929/ordit/capa_ordit/L415_G.npy', '417': ARREL / '4-RESULTATS/v119_20260929/trama/capa_trama/L415_G.npy'}
LNOU = {cid: q_blocs(np.load(RAS_NOU[cid])).astype(np.float32) / 65535 for cid in {c for v in NOVA.values() for c, _ in v}}
TAG = {41: 'P01_NRGF', 42: 'P01_NRGF_extrap', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 47: '03', 49: '07', 51: '04', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
def ras(d, lid):
    for f in (d / f'{TAG[lid]}_u16.npy', d / f'L{lid}_G.npy'):
        if f.exists(): return q_blocs(np.load(f)).astype(np.float32) / 65535
    return None
NOUS = {nom: {lid: r for d in ds for lid in TAG for r in [ras(d, lid)] if r is not None} for nom, ds in VARS.items()}
for nom, cc in NOUS.items(): print(nom, 'capes substituïdes:', sorted(cc), flush=True)
def llenc(lid, c, fill):
    a, org = p.channel(lid, c)
    if a is None: return None
    out = np.full((H, W), fill, np.float32); x, y = org; h, w = a.shape
    xa, ya, xb, yb = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if xb > xa and yb > ya: out[ya:yb, xa:xb] = a[ya - y:yb - y, xa - x:xb - x] / 65535.0
    return out
def alfa(l):
    a = np.full((H, W), l['opacity'] / 255.0, np.float32); t = llenc(l['id'], -1, 0.0)
    if t is not None: a *= t
    if l['mask'] is not None and not l['mask']['disabled']:
        m = llenc(l['id'], -2, l['mask']['background'] / 255.0)
        if m is not None: a *= m
    return a
def fusiona(b, lv, a, mode):
    if mode == 'NORMAL': return b + a * (lv - b)
    if mode == 'MULTIPLY': return b * (1 - a + a * lv)
    if mode == 'OVERLAY': f = np.where(b <= 0.5, 2 * b * lv, 1 - 2 * (1 - b) * (1 - lv)); return b + a * (f - b)
    if mode == 'LIGHTEN': return b + a * (np.maximum(b, lv) - b)
    if mode == 'LINEAR_DODGE': return b + a * (np.minimum(1, b + lv) - b)
def quart(x): return x[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4).mean((1, 3))
L4 = {nom: np.zeros((H // 4, W // 4), np.float32) for nom in ['V115'] + list(VARS)}
for c in range(3):
    piles = {k: None for k in L4}
    for l in PILA:
        lv = llenc(l['id'], c, 0.0); a = alfa(l)
        for k in piles:
            lk = NOUS[k][l['id']] if (k in NOUS and l['id'] in NOUS[k]) else lv
            piles[k] = a * lk if piles[k] is None else fusiona(piles[k], lk, a, l['blend'])
            if l['id'] == 56 and k in NOVA:
                for cid, op in NOVA[k]: piles[k] = fusiona(piles[k], LNOU[cid], np.float32(op), 'OVERLAY')
        del lv, a
    for k in piles: L4[k] += quart(piles[k]) / 3
    del piles
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
G0, V0 = gran(L4['V115']); res = {}
for k, L in L4.items():
    Gk, _ = gran(L); dom = V0 & (rr > 1.2); r_ = (Gk[dom] / np.maximum(G0[dom], 1e-6) - 1) * 100
    res[k] = dict(contrast=contrast(L), terra=terra(L), simetria=simetria(L), canvi_gran_escala=[round(float(np.percentile(r_, q)), 2) for q in (1, 50, 99)])
    np.save(Path(sys.argv[1]).with_name(f'L4_{k}.npy'), L)
res['control Brno 200 (no és criteri)'] = dict(contrast=contrast(np.load(ARREL / '4-RESULTATS/v114_artefactes_foscos_20260929/estadis_1a4/brno_230_L.npy')))
json.dump(dict(nota=__doc__.split('\n')[0], variants={k: [str(x) for x in v] for k, v in VARS.items()}, resultats=res), open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
print('contrast cru (%)'.ljust(34), ' '.join(f'{m["marca"]:>6d}' for m in M))
for k, r in res.items(): print(k[:34].ljust(34), ' '.join(f"{(r['contrast'][m['marca']] or 0):6.2f}" for m in M))
for k, r in res.items():
    if 'terra' not in r: continue
    print(f"{k[:20]:20s} sota el cel {r['terra']['fraccio_sota_cel'] * 100:5.2f} % (p1 {r['terra']['p1']}) · marques sota:", ' '.join(f"{i}:{v['sota']:.2f}" for i, v in r['terra']['marques'].items()))
    print(' ' * 21, 'simetria A per bandes', {b: v['A'] for b, v in r['simetria']['bandes'].items()}, '· canvi gran escala', r['canvi_gran_escala'])
    print(' ' * 21, 'marques z_out/esperat', ' '.join(f"{i}:{v['z_out']:.1f}/{v['esperat']:.1f}" for i, v in r['simetria']['marques'].items()))
