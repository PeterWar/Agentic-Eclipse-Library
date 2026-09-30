"""w5 (V108 · verifica2_negres) · Circularitat: el genoll força el compost suau (6 px) a no baixar del cel SEC (5–5,6 R☉) ni del HQ (6,5–8,4 R☉),
que són justament les dues referències de la mètrica. Aquí es mesuren les zones negres amb referències i escales que el genoll NO fa servir:
suavitzat 2 / 12 / 24 px, cel a 5,6–6,5 R☉ (entremig), cel a 7–8,5 R☉ només dins del marc, 72 sectors. Ús: w5_sensibilitat.py [nom]"""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from w0_comu import *
NOM = sys.argv[1] if len(sys.argv) > 1 else 'CEL_G_MAX_T_e30_W_H0'; PAS = 2
G = geo(pas=PAS); r, th, ok, marc = G['r'], G['th'], G['ok'], G['marc']; Z = ok & marc & (r >= 1.3) & (r < 4.5)
L0 = np.load(OUT / 'L_V107_w0_pas2.npy'); L1 = np.load(OUT / f'L_{NOM}_w0_pas2.npy')
def zona(L, s, ra, rb, vm, ns=36):
    Ls = cv2.GaussianBlur(L, (0, 0), s / PAS) if s > 0 else L; sec = (th * ns / 360).astype(int) % ns; k = vm & (r >= ra) & (r < rb)
    v = np.array([np.median(Ls[k & (sec == i)]) if (k & (sec == i)).sum() > 100 else np.nan for i in range(ns)]); g = np.isfinite(v); ii = np.arange(ns)
    v = np.interp(ii, ii[g], v[g], period=ns); x = th * ns / 360 - 0.5; i0 = np.floor(x).astype(int) % ns; f = x - np.floor(x)
    sky = (1 - f) * v[i0] + f * v[(i0 + 1) % ns]; neg = Z & (Ls < sky)
    return dict(total=round(100 * float(neg.sum() / Z.sum()), 2), b3_4_5=round(100 * float(neg[Z & (r >= 3)].mean()), 2), sectors_amb_cel=int(g.sum()))
C = {'s6_6.5-8.5_llenc (A)': (6, 6.5, 8.5, ok), 's6_5-5.6_marc (B)': (6, 5.0, 5.6, ok & marc), 's6_5.6-6.5_llenc': (6, 5.6, 6.5, ok), 's6_7-8.5_marc': (6, 7.0, 8.5, ok & marc),
     's2_6.5-8.5': (2, 6.5, 8.5, ok), 's12_6.5-8.5': (12, 6.5, 8.5, ok), 's24_6.5-8.5': (24, 6.5, 8.5, ok), 's12_5-5.6_marc': (12, 5.0, 5.6, ok & marc), 's24_5-5.6_marc': (24, 5.0, 5.6, ok & marc)}
res = {k: dict(V107=zona(L0, *v), cand=zona(L1, *v)) for k, v in C.items()}
res['s6_6.5-8.5_72sectors'] = dict(V107=zona(L0, 6, 6.5, 8.5, ok, 72), cand=zona(L1, 6, 6.5, 8.5, ok, 72))
(OUT / f'W5_{NOM}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
for k, v in res.items(): print(f"{k:28s} V107 {v['V107']['total']:6.2f} ({v['V107']['b3_4_5']:6.2f})  →  cand {v['cand']['total']:6.2f} ({v['cand']['b3_4_5']:6.2f})  sectors {v['cand']['sectors_amb_cel']}")
