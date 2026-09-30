"""vn5 (V108 · verificador de «negres») · Detall del COMPOST emulat (pas 2) V107 contra CEL_TER_Q: energia DoG de ln L per escales i bandes,
i contrast buit/plomall separat per signe (mitjana de la part negativa i positiva del pas alt 4–64 px). Sortida: VN5.json"""
import sys, json
from pathlib import Path
import numpy as np, cv2
R0 = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v108_20260926/verifica_negres'))
import vn1_psb_i_emulacio as V
OUT = V.OUT; res = {}
L = {k: np.log(np.maximum(np.load(OUT / f'L_emul_{k}_pas2.npy'), 1e-3)).astype(np.float32) for k in ('V107', 'CEL_TER_Q')}
def dog(a, s1, s2): return (a if s1 == 0 else cv2.GaussianBlur(a, (0, 0), s1)) - cv2.GaussianBlur(a, (0, 0), s2)
ok = V.ZONA | (V.marc & ~V.lluna & (V.r >= 4.5) & (V.r < 7))
for esc, (s1, s2) in {'2-8px': (1, 4), '8-32px': (4, 16), '32-128px': (16, 64), 'pa_4-64px': (2, 32)}.items():
    D = {k: dog(v, s1, s2) for k, v in L.items()}; e = {}
    for a, b in ((1.3, 2), (2, 3), (3, 4.5), (4.5, 7)):
        m = ok & (V.r >= a) & (V.r < b); v0, v1 = D['V107'][m], D['CEL_TER_Q'][m]
        d = dict(energia=float(np.sqrt(np.mean(v1 ** 2)) / np.sqrt(np.mean(v0 ** 2))), corr=float(np.corrcoef(v0, v1)[0, 1]))
        if esc == 'pa_4-64px':
            d.update(buits_mitj_neg=[float(v0[v0 < 0].mean()), float(v1[v1 < 0].mean())], plomalls_mitj_pos=[float(v0[v0 > 0].mean()), float(v1[v1 > 0].mean())],
                     p10=[float(np.percentile(v0, 10)), float(np.percentile(v1, 10))], p90=[float(np.percentile(v0, 90)), float(np.percentile(v1, 90))])
        e[f'{a:g}-{b:g}'] = d
    res[esc] = e
(OUT / 'VN5.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n'); print(json.dumps(res, ensure_ascii=False, indent=1))
