"""c1 (V116) · Comprovació: el render natiu del pas 1 (sota la 301) coincideix amb la meva composició amb la 415 (Superposar 40 % damunt de la 56) i NO sense ella.
Finestra x 5950–7050, y 4300–4750 (fora de la caixa de la 301). Composició amb la matemàtica de fusió de e2/e3 sobre el PSB de pas (stage1.psb)."""
import sys, json, numpy as np, tifffile
from pathlib import Path
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v116_20260929'
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB
X0, X1, Y0, Y1 = 5950, 7050, 4300, 4750
p = PSB(str(O / 'stage1.psb'))
AMAGA = {301, 239, 240, 241, 242, 243, 244, 202, 234, 308, 230, 231, 232, 62, 233, 203, 414}
PILA = [l for l in p.layers if l['visible'] and l['right'] > l['left'] and l['id'] not in AMAGA]
print('pila', [l['id'] for l in PILA])
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
rn = np.asarray(tifffile.memmap(O / 'render_stage1_sota301/visible_complet.tif', mode='r')[Y0:Y1, X0:X1], np.float32) / 65535
out = {}
for nom, amb in (('amb_415', True), ('sense_415', False)):
    d = []
    for c in range(3):
        b = None
        for l in PILA:
            if l['id'] == 415 and not amb: continue
            lv = fin(l['id'], c, 0.0); a = alfa(l); b = a * lv if b is None else fusiona(b, lv, a, l['blend'])
        d.append(np.abs(b - rn[..., c]) * 65535)
    d = np.stack(d, -1); out[nom] = dict(mitjana_DN=round(float(d.mean()), 2), p99_DN=round(float(np.percentile(d, 99)), 1), max_DN=round(float(d.max()), 1))
    print(nom, out[nom], flush=True)
ok = out['amb_415']['mitjana_DN'] < 0.5 * out['sense_415']['mitjana_DN']; out['PASSA'] = bool(ok); print('PASSA' if ok else 'FALLA')
(O / 'C1_RENDER_415.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
