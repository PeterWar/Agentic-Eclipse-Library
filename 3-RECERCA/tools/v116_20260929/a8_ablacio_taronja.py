"""a8 (V116, 29-09-2026) · Atribució de la línia fosca de la marca taronja al compost: la pila de la V115 de Pere sota els ajustos (capes visibles sota la 239,
sense la 414), composta a la finestra x 5950–7050, y 4300–4750 amb la matemàtica de fusió del Photoshop (com e2/e3), i la mateixa pila traient UNA capa cada cop.
Mesura: clot estret al perfil perpendicular al traç (a6): P(o*) − mitjana(P a |o − o*| ∈ [12, 40]), o* = +5 px, en % del compost (contrast cru).
També la pila candidata de la V116 (41/42 i 45/46 noves, 415 al 40 %). Sortida: taronja/A8_ABLACIO.json"""
import sys, json, numpy as np
from pathlib import Path
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v116_20260929'
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, q_blocs
X0, X1, Y0, Y1 = 5950, 7050, 4300, 4750
p = PSB(str(R / '1-PHOTOSHOP/V115.psb')); H, W = p.height, p.width
PILA = [l for l in p.layers if l['visible'] and l['right'] > l['left'] and l['i'] < p.layer(239)['i'] and l['id'] != 414]
lab = np.asarray(np.load(O / 'marques_V115_etiquetes.npy', mmap_mode='r')[Y0:Y1, X0:X1]) == 11
cols = np.nonzero(lab.any(0))[0]; yc = np.array([np.nonzero(lab[:, c])[0].mean() for c in cols])
def fin(lid, c, fill):
    a, (x, y) = p.channel(lid, c)
    if a is None: return None
    out = np.full((Y1 - Y0, X1 - X0), fill, np.float32); h, w = a.shape
    ya, yb, xa, xb = max(Y0, y), min(Y1, y + h), max(X0, x), min(X1, x + w)
    if yb > ya and xb > xa: out[ya - Y0:yb - Y0, xa - X0:xb - X0] = a[ya - y:yb - y, xa - x:xb - x] / (255.0 if a.dtype == np.uint8 else 65535.0)
    return out
def alfa(l):
    a = np.full((Y1 - Y0, X1 - X0), l['opacity'] / 255.0, np.float32); t = fin(l['id'], -1, 0.0)
    if t is not None: a *= t
    if l['mask'] is not None and not l['mask']['disabled']:
        m = fin(l['id'], -2, l['mask']['background'] / 255.0)
        if m is not None: a *= m
    return a
def fusiona(b, lv, a, mode):
    if mode == 'NORMAL': return b + a * (lv - b)
    if mode == 'MULTIPLY': return b * (1 - a + a * lv)
    if mode == 'OVERLAY': f = np.where(b <= 0.5, 2 * b * lv, 1 - 2 * (1 - b) * (1 - lv)); return b + a * (f - b)
    if mode == 'LIGHTEN': return b + a * (np.maximum(b, lv) - b)
    if mode == 'LINEAR_DODGE': return b + a * (np.minimum(1, b + lv) - b)
TAG = {41: 'P01_NRGF', 42: 'P01_NRGF_extrap', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native'}
NG = O / 'nrgf_s800_415/Lk0_G_MAX_T_e30_W_H0_SUP'; RH = O / 'rhefL/k0_s800'
def nou(lid): d = NG if lid in (41, 42) else RH; return q_blocs(np.asarray(np.load(d / f'{TAG[lid]}_u16.npy', mmap_mode='r')[Y0:Y1, X0:X1])).astype(np.float32) / 65535
L415 = q_blocs(np.asarray(np.load(O / 'AB/capa415/L415_G.npy', mmap_mode='r')[Y0:Y1, X0:X1])).astype(np.float32) / 65535
CAS = ['V115'] + [f'V115 sense {l["id"]}' for l in PILA if l['id'] != 3] + ['V116 candidata', 'V116 candidata sense 415', 'V116 sense 55', 'V116 sense 56', 'V116 sense 55 i 56']
acc = {k: np.zeros((Y1 - Y0, X1 - X0), np.float32) for k in CAS}
cache = {}
for c in range(3):
    pil = {k: None for k in CAS}
    for l in PILA:
        lid = l['id']; lv = fin(lid, c, 0.0); a = alfa(l); ln = nou(lid) if lid in TAG else lv
        for k in CAS:
            v116 = k.startswith('V116'); x = ln if v116 else lv
            treu = (k == f'V115 sense {lid}') or (k == 'V116 sense 55' and lid == 55) or (k == 'V116 sense 56' and lid == 56) or (k == 'V116 sense 55 i 56' and lid in (55, 56))
            if pil[k] is None: pil[k] = a * x; continue
            if not treu: pil[k] = fusiona(pil[k], x, a, l['blend'])
            if lid == 56 and v116 and k != 'V116 candidata sense 415': pil[k] = fusiona(pil[k], L415, np.float32(0.40), 'OVERLAY')
    for k in CAS: acc[k] += np.asarray(pil[k]) * (0.25 if c != 1 else 0.5)
offs = np.arange(-60, 61); res = {}
for k, Lm in acc.items():
    x = np.log(np.maximum(Lm, 1e-5)); P = np.array([np.mean(x[np.clip(np.round(yc + o).astype(int), 0, Y1 - Y0 - 1), cols]) for o in offs]) * 100
    P -= np.polyval(np.polyfit(offs, P, 2), offs)      # treu el gradient suau perpendicular
    o5 = offs == 5; fons = (np.abs(offs - 5) >= 12) & (np.abs(offs - 5) <= 40)
    res[k] = dict(clot_o5_pct=round(float(P[o5][0] - P[fons].mean()), 3), soroll=round(float(P[fons].std()), 3))
    print(f'{k:28s} clot a o=+5: {res[k]["clot_o5_pct"]:+.2f} %  (soroll {res[k]["soroll"]:.2f})', flush=True)
(O / 'taronja/A8_ABLACIO.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
