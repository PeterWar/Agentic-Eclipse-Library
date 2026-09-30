"""a3 (29-09-2026) · On neix cada marca fosca de Pere: la pila de la V114 recomposta en Python (fusions del Photoshop en l'espai del document),
pis a pis, fins a sota les capes d'ajust (S0), comparada amb el compost desat (U, amb els ajustos de Pere) i amb Brno (230–233, jutge).
Mesura per marca: contrast = nivell mitjà a la marca / nivell mitjà a l'anell que l'envolta (60–300 px fora de la marca) − 1, per canal i en lluminància.
Sortides: DESCOMPOSICIO_MARQUES.json i estadis_1a4/<pis>_L.npy (lluminància de cada pis a 1/4, per a les vistes).
Fusions (valors 0–1 del fitxer; α = opacitat · màscara · transparència): Normal b+α(l−b); Multiplicar b(1−α+αl); Superposar b+α(f−b) amb
f = 2bl (b ≤ ½) o 1−2(1−b)(1−l); Aclarir max; Sobreexposició lineal min(1, b+l)."""
import sys, json, numpy as np
from pathlib import Path
from scipy import ndimage as ndi
ARREL = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
OUT = ARREL / '4-RESULTATS/v114_artefactes_foscos_20260929'; (OUT / 'estadis_1a4').mkdir(exist_ok=True)
p = PSB(str(ARREL / '1-PHOTOSHOP/V114.psb')); H, W = p.height, p.width
lab = np.load(OUT / 'marques_414_etiquetes.npy'); M = json.load(open(OUT / 'MARQUES_414.json'))['marques']
PILA = [l for l in p.layers if l['visible'] and l['id'] not in (414,) and l['right'] > l['left']]   # capes de píxels visibles, d'avall a dalt
AJUST = [239, 240, 241, 242, 243, 244]
fins_ajust = [l['id'] for l in PILA if l['i'] < p.layer(239)['i']]
print('pila fins als ajustos:', fins_ajust)

def llenc(lid, c, fill):
    a, org = p.channel(lid, c)
    if a is None: return None
    out = np.full((H, W), fill, np.float32); x, y = org; h, w = a.shape
    xa, ya, xb, yb = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if xb > xa and yb > ya: out[ya:yb, xa:xb] = a[ya - y:yb - y, xa - x:xb - x] / 65535.0
    return out
def alfa(l):
    a = np.full((H, W), l['opacity'] / 255.0, np.float32)
    t = llenc(l['id'], -1, 0.0)
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
    raise ValueError(mode)
def quart(x): return x[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4).mean((1, 3))

# anells de comparació per marca (a 1/4): marca = etiqueta; veïnat = 60–300 px fora de la marca (i dins de la dada)
lab4 = lab[:H // 4 * 4:4, :W // 4 * 4:4]
dist = {m['marca']: ndi.distance_transform_edt(lab4 != m['marca']) * 4 for m in M}
def contrast(L4, valid4):
    out = {}
    for m in M:
        k = m['marca']; dins = (lab4 == k) & valid4; fora = (dist[k] > 60) & (dist[k] < 300) & (lab4 == 0) & valid4
        out[k] = round(float(L4[dins].mean() / L4[fora].mean() - 1), 4) if dins.any() and fora.any() else None
    return out

etapes = {}                                           # pis → lluminància a 1/4
for c in range(3):                                   # canal a canal i α al vol: memòria acotada (~2 GB)
    b = None
    for l in PILA:
        if l['id'] not in fins_ajust: continue
        lv = llenc(l['id'], c, 0.0); a = alfa(l)
        b = a * lv if b is None else fusiona(b, lv, a, l['blend'])   # la base (Normal sobre transparent)
        del lv, a
        etapes.setdefault(f"{l['id']:03d}", [None, None, None])[c] = quart(b)
    del b
S0_4 = None
valid4 = quart((p.composite()[..., :3].astype(np.float32).mean(2) / 65535) > 0.004) > 0.99
res = {}
for key, ch in etapes.items():
    L4 = np.mean(ch, 0); np.save(OUT / f'estadis_1a4/{key}_L.npy', L4.astype(np.float32)); res[key] = contrast(L4, valid4)
S0_4 = np.mean(etapes[max(etapes)], 0)
U = np.load(OUT / 'U_compost_sense_414_u16.npy', mmap_mode='r')
U4 = np.mean([quart(U[..., c].astype(np.float32) / 65535) for c in range(3)], 0); np.save(OUT / 'estadis_1a4/U_L.npy', U4.astype(np.float32))
res['U (amb els ajustos de Pere)'] = contrast(U4, valid4)
for bid in (230, 231, 232, 233):
    l = p.layer(bid); Lb = np.mean([llenc(bid, c, 0.0) for c in range(3)], 0); tb = llenc(bid, -1, 0.0)
    vb = quart((Lb > 0.004) & ((tb if tb is not None else 1) > 0.5)) > 0.99
    Lb4 = quart(Lb); np.save(OUT / f'estadis_1a4/brno_{bid}_L.npy', Lb4.astype(np.float32)); res[f"Brno {bid} · {l['name'][:24]}"] = contrast(Lb4, vb & valid4)
noms = {f"{l['id']:03d}": f"{l['id']} {l['blend']} {l['opacity']}/255 · {l['name'][:30]}" for l in PILA}
json.dump(dict(nota='contrast = nivell a la marca / nivell al veïnat (60–300 px) − 1, lluminància mitjana de R, G, B; pisos acumulats d\'avall a dalt fins a sota els ajustos',
               pisos={noms.get(k, k): v for k, v in res.items()}), open(OUT / 'DESCOMPOSICIO_MARQUES.json', 'w'), ensure_ascii=False, indent=1)
print('pis'.ljust(56), ' '.join(f'{m["marca"]:>6d}' for m in M))
for k, v in res.items(): print(noms.get(k, k)[:56].ljust(56), ' '.join(f"{(v[m['marca']] or 0) * 100:6.2f}" for m in M))
