"""a1 (V116, 29-09-2026) · Dues mesures NOMÉS amb la nostra dada (Brno queda per al control final):
 (1) Descomposició pis a pis de la pila d'un PSB (fusions del Photoshop, sota els ajustos de Pere) a les 11 marques de Pere (MARQUES_V115.json):
     contrast cru = nivell a la marca / nivell a l'anell de 60–300 px − 1, a cada pis, i al compost desat (U, render natiu sense la 414).
 (2) SIMETRIA DEL GUANY: el realç ha d'amplificar igual l'estructura fosca que la clara. Per bandes de radi, d_in = ln L_base(σ8) − ln L_base(σ150)
     i d_out = el mateix a la sortida (S0 o U); per quantils de d_in, la mediana de d_out; pendent g− (d_in < 0) i g+ (d_in > 0) per mínims quadrats
     ponderats per l'origen. Asimetria A = g−/g+: A > 1 vol dir foscor inventada (els buits s'aprofundeixen més que no s'aclareixen els raigs).
Ús: a1_descomposicio_i_simetria.py <psb> <render_U.tif> <sortida.json> [--brno]"""
import sys, json, numpy as np, tifffile
from pathlib import Path
from scipy import ndimage as ndi
ARREL = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
O = ARREL / '4-RESULTATS/v116_20260929'
PSBP, TIF, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve(); BRNO = '--brno' in sys.argv
p = PSB(str(PSBP)); H, W = p.height, p.width
lab = np.load(O / 'marques_V115_etiquetes.npy'); M = json.load(open(O / 'MARQUES_V115.json'))['marques']
PILA = [l for l in p.layers if l['visible'] and l['right'] > l['left'] and l['i'] < p.layer(239)['i']]
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
et = {}
for c in range(3):
    b = None
    for l in PILA:
        lv = llenc(l['id'], c, 0.0); a = alfa(l); b = a * lv if b is None else fusiona(b, lv, a, l['blend']); del lv, a
        et.setdefault(l['id'], np.zeros((H // 4, W // 4), np.float32)); et[l['id']] += quart(b) / 3
    del b
U = (np.load(TIF, mmap_mode="r") if TIF.suffix == ".npy" else tifffile.memmap(TIF, mode="r")); U4 = np.mean([quart(np.asarray(U[..., c], np.float32) / 65535) for c in range(3)], 0)
lab4 = lab[:H // 4 * 4:4, :W // 4 * 4:4]; dist = {m['marca']: ndi.distance_transform_edt(lab4 != m['marca']) * 4 for m in M}
def contrast(L4):
    v4 = L4 > 0.004; o = {}
    for m in M:
        k = m['marca']; d = (lab4 == k) & v4; f = (dist[k] > 60) & (dist[k] < 300) & (lab4 == 0) & v4
        o[k] = round(float(L4[d].mean() / L4[f].mean() - 1) * 100, 2) if d.any() and f.any() else None
    return o
noms = {l['id']: f"{l['id']} {l['blend']} {l['opacity']}/255 · {l['name'][:28]}" for l in PILA}
res = dict(pisos={noms[k]: contrast(v) for k, v in et.items()}, U=contrast(U4))
SOL = (5361.768 / 4, 3775.748 / 4); RS = 440.603 / 4; yy, xx = np.mgrid[0:H // 4, 0:W // 4]; rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
def dev(L):
    v = L > 0.004; s = ndi.gaussian_filter(np.where(v, L, 0), 2) / np.maximum(ndi.gaussian_filter(v.astype(np.float32), 2), 1e-6)
    bg = ndi.gaussian_filter(np.where(v, L, 0), 37.5) / np.maximum(ndi.gaussian_filter(v.astype(np.float32), 37.5), 1e-6)
    return np.where(v, np.log(np.maximum(s, 1e-6)) - np.log(np.maximum(bg, 1e-6)), np.nan)
din = dev(et[3])
def simetria(Lout, bandes=((1.3, 2.0), (2.0, 3.5), (3.5, 5.5), (5.5, 9.0))):
    dout = dev(Lout); o = {}
    for a_, b_ in bandes:
        k = (rr > a_) & (rr < b_) & np.isfinite(din) & np.isfinite(dout)
        x, y = din[k], dout[k]; q = np.quantile(x, np.linspace(0.02, 0.98, 49)); xm, ym = [], []
        for lo, hi in zip(q[:-1], q[1:]):
            s = (x >= lo) & (x < hi)
            if s.sum() > 50: xm.append(np.median(x[s])); ym.append(np.median(y[s]))
        xm, ym = np.array(xm), np.array(ym); neg, pos = xm < 0, xm > 0
        gm = float(np.sum(xm[neg] * ym[neg]) / np.sum(xm[neg] ** 2)); gp = float(np.sum(xm[pos] * ym[pos]) / np.sum(xm[pos] ** 2))
        o[f'{a_}-{b_}'] = dict(g_fosc=round(gm, 3), g_clar=round(gp, 3), asimetria=round(gm / gp, 3), sd_in=round(float(np.std(x)), 5))
    return o
res['simetria_S0'] = simetria(et[max(k for k in et if k != 414)] if False else et[PILA[-1]['id']])
res['simetria_U'] = simetria(U4)
if BRNO:
    Bb = np.load(ARREL / '4-RESULTATS/v114_artefactes_foscos_20260929/estadis_1a4/brno_230_L.npy'); res['control_Brno'] = dict(contrast=contrast(Bb))
json.dump(dict(psb=str(PSBP.relative_to(ARREL)), render=str(TIF.relative_to(ARREL)), nota='contrast cru en %; simetria: g = pendent de d_out contra d_in (base) per al costat fosc i el clar', resultats=res), open(OUT, 'w'), ensure_ascii=False, indent=1)
print('pis'.ljust(50), ' '.join(f'{m["marca"]:>6d}' for m in M))
for k, v in list(res['pisos'].items()) + [('U (compost desat)', res['U'])] + ([('Brno (control)', res['control_Brno']['contrast'])] if BRNO else []):
    print(k[:50].ljust(50), ' '.join(f"{(v[m['marca']] if v[m['marca']] is not None else 0):6.2f}" for m in M))
for k in ('simetria_S0', 'simetria_U'): print(k, json.dumps(res[k], ensure_ascii=False))
