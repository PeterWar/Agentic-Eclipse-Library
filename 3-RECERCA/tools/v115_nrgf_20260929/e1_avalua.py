"""e1 (V115, 29-09-2026) · Avaluació d'una variant de la NRGF (41/42) sobre la pila de la V114 de Pere, contra el jutge (Brno 200 mm).
La pila sota els ajustos de Pere es recompon en Python (fusions del Photoshop, com a v114_artefactes_foscos/a3) amb la 41 i la 42 d'una variant
(ràster monocrom q(u16) als tres canals; alfa i màscara, les de la V114) i la resta de capes tal com són a la V114. Mesures, en unitats de la σ de
textura de cada imatge (D = ln nivell σ8 − ln fons σ300, anell 4,5–9,5 R☉): (1) el percentil 10 de D dins de cada marca de Pere (414); (2) les cues de
D a 2–9 R☉ fora del limbe (p1, p5 fosques; p95, p99 clares), per veure que es cura el costat fosc sense tocar el clar.
Ús: e1_avalua.py <sortida.json> <nom=carpeta[+carpeta…]> [...]   (cada carpeta aporta les capes 41/42/45/46 de les quals porti el ràster)"""
import sys, json, numpy as np
from pathlib import Path
from scipy import ndimage as ndi
ARREL = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, q_blocs
MARQ = ARREL / '4-RESULTATS/v114_artefactes_foscos_20260929'
p = PSB(str(ARREL / '1-PHOTOSHOP/V114.psb')); H, W = p.height, p.width
lab = np.load(MARQ / 'marques_414_etiquetes.npy'); M = json.load(open(MARQ / 'MARQUES_414.json'))['marques']
PILA = [l for l in p.layers if l['visible'] and l['right'] > l['left'] and l['i'] < p.layer(239)['i']]
VARS = {a.split('=')[0]: [Path(x) for x in a.split('=')[1].split('+')] for a in sys.argv[2:]}
TAG = {41: 'P01_NRGF', 42: 'P01_NRGF_extrap', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native'}
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
NOUS = {nom: {lid: q_blocs(np.load(d / f'{TAG[lid]}_u16.npy')).astype(np.float32) / 65535 for d in ds for lid in TAG if (d / f'{TAG[lid]}_u16.npy').exists()} for nom, ds in VARS.items()}
for nom, cc in NOUS.items(): print(nom, 'capes substituïdes:', sorted(cc), flush=True)
L4 = {nom: np.zeros((H // 4, W // 4), np.float32) for nom in ['V114'] + list(VARS)}
for c in range(3):
    piles = {k: None for k in L4}
    for l in PILA:
        lv = llenc(l['id'], c, 0.0); a = alfa(l)
        for k in piles:
            lk = NOUS[k][l['id']] if (k in NOUS and l['id'] in NOUS[k]) else lv
            piles[k] = a * lk if piles[k] is None else fusiona(piles[k], lk, a, l['blend'])
        del lv, a
    for k in piles: L4[k] += quart(piles[k]) / 3
    del piles
lab4 = lab[:H // 4 * 4:4, :W // 4 * 4:4]; SOL = (5361.768 / 4, 3775.748 / 4); RS = 440.603 / 4
yy, xx = np.mgrid[0:H // 4, 0:W // 4]; rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
def D(L):
    v = L > 0.004; num = ndi.gaussian_filter(np.where(v, L, 0), 75); den = ndi.gaussian_filter(v.astype(np.float32), 75)
    s = ndi.gaussian_filter(np.where(v, L, 0), 2) / np.maximum(ndi.gaussian_filter(v.astype(np.float32), 2), 1e-6)
    return np.where(v & (den > 0.5), np.log(np.maximum(s, 1e-6)) - np.log(np.maximum(num / np.maximum(den, 1e-6), 1e-6)), np.nan)
BR = np.load(MARQ / 'estadis_1a4/brno_230_L.npy')
dist = {m['marca']: ndi.distance_transform_edt(lab4 != m['marca']) * 4 for m in M}
def contrast(L4):
    v4 = L4 > 0.004; o = {}
    for m in M:
        k = m['marca']; d = (lab4 == k) & v4; f = (dist[k] > 60) & (dist[k] < 300) & (lab4 == 0) & v4
        o[k] = round(float(L4[d].mean() / L4[f].mean() - 1) * 100, 2) if d.any() and f.any() else None
    return o
def gran(L):
    v = L > 0.004; return ndi.gaussian_filter(np.where(v, L, 0), 75) / np.maximum(ndi.gaussian_filter(v.astype(np.float32), 75), 1e-6), v
G114, V114v = gran(L4['V114'])
res = {}
for k, L in list(L4.items()) + [('Brno 200 (jutge)', BR)]:
    d = D(L); an = (rr > 4.5) & (rr < 9.5) & (lab4 == 0) & np.isfinite(d); sd = float(np.nanstd(d[an]))
    cor = (rr > 2) & (rr < 9) & np.isfinite(d)
    if k != 'Brno 200 (jutge)': cor &= np.isfinite(D(BR))            # mateix domini que el jutge
    z = d[cor] / sd
    res[k] = dict(sigma_pct=round(sd * 100, 3), cua_p1=round(float(np.percentile(z, 1)), 2), cua_p5=round(float(np.percentile(z, 5)), 2),
                  cua_p95=round(float(np.percentile(z, 95)), 2), cua_p99=round(float(np.percentile(z, 99)), 2),
                  marques={m['marca']: round(float(np.nanpercentile(d[(lab4 == m['marca']) & np.isfinite(d)], 10)) / sd, 2) for m in M}, contrast_pct=contrast(L))
    if k in L4:
        np.save(Path(sys.argv[1]).with_name(f'L4_{k}.npy'), L4[k]); Gk, _ = gran(L); dom = V114v & (rr > 1.2)
        r_ = (Gk[dom] / np.maximum(G114[dom], 1e-6) - 1) * 100; res[k]['canvi_gran_escala_pct'] = [round(float(np.percentile(r_, q)), 2) for q in (1, 50, 99)]
json.dump(dict(nota='D en unitats de σ de textura (4,5–9,5 R☉); marques = percentil 10 dins la marca; cues a 2–9 R☉ (domini de Brno)', variants={k: [str(x) for x in v] for k, v in VARS.items()}, resultats=res),
          open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
print('variant'.ljust(22), 'σ%   p1    p5   p95   p99 |', ' '.join(f'{m["marca"]:>6d}' for m in M))
for k, r in res.items():
    print(k[:22].ljust(22), f"{r['sigma_pct']:.2f} {r['cua_p1']:5.2f} {r['cua_p5']:5.2f} {r['cua_p95']:5.2f} {r['cua_p99']:5.2f} |", ' '.join(f"{r['marques'][m['marca']]:6.2f}" for m in M))
print('canvi de gran escala respecte de la V114 (σ 300 px; p1 / p50 / p99, %):', {k: r.get('canvi_gran_escala_pct') for k, r in res.items() if 'canvi_gran_escala_pct' in r})
print('contrast cru (marca / anell 60–300 px − 1, %)'.ljust(52), ' '.join(f'{m["marca"]:>6d}' for m in M))
for k, r in res.items(): print(k[:52].ljust(52), ' '.join(f"{(r['contrast_pct'][m['marca']] or 0):6.2f}" for m in M))
