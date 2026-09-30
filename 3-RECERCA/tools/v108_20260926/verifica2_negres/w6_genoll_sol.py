"""w6 (V108 · verifica2_negres) · El GENOLL SOL: compost de la recomanada contra el del CEL sol (candidats_v2/CEL), tots dos amb el compositor w0.
Rectificació de l'estructura de zona (pas alt 6–64 px de ln L): cua fosca (p1, p5) contra cua clara (p95, p99) i asimetria, per bandes;
fracció de píxels on el compost suau (6 px) queda A MENYS D'UN 0,2 % de la seva mediana local de 64 px (apilament contra un terra)."""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from w0_comu import *
PAS = 2; G = geo(pas=PAS); r, ok, marc, dl = G['r'], G['ok'], G['marc'], G['dl']
La = np.load(OUT / 'L_CEL_w0_pas2.npy'); Lb = np.load(OUT / 'L_CEL_G_MAX_T_e30_W_H0_w0_pas2.npy'); L0 = np.load(OUT / 'L_V107_w0_pas2.npy')
def resid(L): l = np.log(np.maximum(L, 1e-4)); return cv2.GaussianBlur(l, (0, 0), 3.0) - cv2.GaussianBlur(l, (0, 0), 32.0)
Ra, Rb, R0_ = resid(La), resid(Lb), resid(L0); res = {}
sk = lambda x: float(np.mean((x - x.mean()) ** 3) / np.std(x) ** 3)
for a_, b_ in ((2, 3), (3, 4.5), (4.5, 7), (7, 9.5)):
    m = ok & marc & (r >= a_) & (r < b_) & (dl > 60); o = {}
    for nom, R in (('V107', R0_), ('CEL_sol', Ra), ('recomanada', Rb)):
        q = np.percentile(R[m], [1, 5, 50, 95, 99]); o[nom] = dict(p1=float(q[0] - q[2]), p5=float(q[1] - q[2]), p95=float(q[3] - q[2]), p99=float(q[4] - q[2]), asimetria=sk(R[m]), rms=float(R[m].std()))
    o['genoll_sol_quocients'] = {k: round(o['recomanada'][k] / o['CEL_sol'][k], 4) for k in ('p1', 'p5', 'p95', 'p99', 'rms')}
    res[f'{a_:g}-{b_:g}'] = o
(OUT / 'W6_GENOLL_SOL.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
for k, v in res.items(): print(k, v['genoll_sol_quocients'], 'asim CEL', round(v['CEL_sol']['asimetria'], 3), 'rec', round(v['recomanada']['asimetria'], 3))
