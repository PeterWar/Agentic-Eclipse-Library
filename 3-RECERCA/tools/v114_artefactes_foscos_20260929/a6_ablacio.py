"""a6 (29-09-2026) · Ablació: la pila de la V114 sota els ajustos (S0), recomposta sense una capa (o un grup) cada vegada, i la profunditat de cada marca
en unitats de la seva pròpia textura (σ de D a l'anell 4,5–9,5 R☉), com a PROFUNDITAT_EN_SIGMA.json, per comparar amb Brno 200 mm.
Una capa que fa l'excés respecte de Brno és la que, en treure-la, acosta la marca a Brno sense perdre la textura. Sortida: ABLACIO.json."""
import sys, json, numpy as np
from pathlib import Path
from scipy import ndimage as ndi
ARREL = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
OUT = ARREL / '4-RESULTATS/v114_artefactes_foscos_20260929'
p = PSB(str(ARREL / '1-PHOTOSHOP/V114.psb')); H, W = p.height, p.width
lab = np.load(OUT / 'marques_414_etiquetes.npy'); M = json.load(open(OUT / 'MARQUES_414.json'))['marques']
PILA = [l for l in p.layers if l['visible'] and l['right'] > l['left'] and l['i'] < p.layer(239)['i']]
ABL = {'cap (S0)': [], 'sense 46 RHEF 30°': [46], 'sense 45 i 46 RHEF': [45, 46], 'sense 41 i 42 NRGF': [41, 42], 'sense 47 i 49 ACHF azimutals': [47, 49],
       'sense 56 WOW bilateral': [56], 'sense 55 WOW': [55], 'sense 54 MGN': [54], 'sense 51 ACHF micro': [51]}
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
# les capes es llegeixen una vegada per canal i es fan servir per a totes les ablacions (memòria: una pila per ablació, a 1/4 només el resultat)
L4 = {k: np.zeros((H // 4, W // 4), np.float32) for k in ABL}
for c in range(3):
    piles = {k: None for k in ABL}
    for l in PILA:
        lv = llenc(l['id'], c, 0.0); a = alfa(l)
        for k, treu in ABL.items():
            if l['id'] in treu: continue
            piles[k] = a * lv if piles[k] is None else fusiona(piles[k], lv, a, l['blend'])
        del lv, a
    for k in ABL: L4[k] += quart(piles[k]) / 3
    del piles
lab4 = lab[:H // 4 * 4:4, :W // 4 * 4:4]; SOL = (5361.768 / 4, 3775.748 / 4); RS = 440.603 / 4
yy, xx = np.mgrid[0:H // 4, 0:W // 4]; rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
def D(L):
    v = L > 0.004; num = ndi.gaussian_filter(np.where(v, L, 0), 75); den = ndi.gaussian_filter(v.astype(np.float32), 75)
    s = ndi.gaussian_filter(np.where(v, L, 0), 2) / np.maximum(ndi.gaussian_filter(v.astype(np.float32), 2), 1e-6)
    return np.where(v & (den > 0.5), np.log(np.maximum(s, 1e-6)) - np.log(np.maximum(num / np.maximum(den, 1e-6), 1e-6)), np.nan)
res = {}
for k, L in list(L4.items()) + [('Brno 200 (jutge)', np.load(OUT / 'estadis_1a4/brno_230_L.npy'))]:
    d = D(L); an = (rr > 4.5) & (rr < 9.5) & (lab4 == 0) & np.isfinite(d); sd = float(np.nanstd(d[an]))
    res[k] = {'σ': round(sd * 100, 2)}
    for m in M:
        dins = (lab4 == m['marca']) & np.isfinite(d); res[k][m['marca']] = round(float(np.nanpercentile(d[dins], 10)) / sd, 2)
json.dump(dict(nota='percentil 10 de D dins de cada marca en unitats de la σ de textura (4,5–9,5 R☉) de la mateixa imatge; pila sota els ajustos de Pere', ablacio=res),
          open(OUT / 'ABLACIO.json', 'w'), ensure_ascii=False, indent=1)
print('ablació'.ljust(30), 'σ %  ', ' '.join(f'{m["marca"]:>6d}' for m in M))
for k, d in res.items(): print(k.ljust(30), f"{d['σ']:5.2f}", ' '.join(f"{d[m['marca']]:6.2f}" for m in M))
