"""j14c (V99 banda, objecció de Codex 25-09) · J14 (anells a 1–9 px i lupa) de dues versions sobre EXACTAMENT els mateixos píxels: el domini
físic de la V98 (A3B) ∩ alfa ≥ 0,99 a TOTES DUES versions. Ús: j14c_suport_i_alfa_comuns.py <carpeta_filtres_A> <carpeta_filtres_B> <sortida.json>"""
import sys, json
from pathlib import Path
import numpy as np
T98 = Path(__file__).resolve().parents[1] / 'v98_20260925'; sys.path.insert(0, str(T98))
A, B, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); sys.argv = sys.argv[:1]
import j14_anells_lupa as J
ARREL = Path(__file__).resolve().parents[3]
Q = np.load(ARREL / '4-RESULTATS/v98_20260925/lineal_v98_franja/A3B_franja_neta.npz'); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]
x0, y0, x1, y1 = J.box; J.zona = J.zona & np.asarray(Q['domini'])[y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]
rep = {}
for lid, tag in J.TAG.items():
    ua = np.load(A / f'{tag}_u16.npy', mmap_mode='r')[y0:y1, x0:x1].astype(np.float32) / 65535; aa = np.load(A / f'{tag}_alfa_u16.npy', mmap_mode='r')[y0:y1, x0:x1].astype(np.float32) / 65535
    ub = np.load(B / f'{tag}_u16.npy', mmap_mode='r')[y0:y1, x0:x1].astype(np.float32) / 65535; ab = np.load(B / f'{tag}_alfa_u16.npy', mmap_mode='r')[y0:y1, x0:x1].astype(np.float32) / 65535
    al = np.minimum(aa, ab); an_a, lu_a = J.mesura(ua, al); an_b, lu_b = J.mesura(ub, al)
    ca = min(v['clot'] for v in an_a.values()); cb = min(v['clot'] for v in an_b.values())
    pitjors = sorted([(an_b[s]['clot'] - an_a[s]['clot'], s, an_a[s]['clot'], an_b[s]['clot'], an_b[s]['d_px']) for s in an_b if s in an_a])[:3]
    rep[lid] = dict(tag=tag, clot_A=ca, clot_B=cb, lupa_med_A=float(np.median([v['index'] for v in lu_a.values() if v['index']])), lupa_med_B=float(np.median([v['index'] for v in lu_b.values() if v['index']])),
                    sectors_que_mes_empitjoren=pitjors, anells_A=an_a, anells_B=an_b)
    print(lid, tag[:14].ljust(14), f'clot {ca:+.4f} → {cb:+.4f}', ' pitjors (Δ, sector, A, B, d):', [(round(p[0], 3), p[1], p[2], p[3], p[4]) for p in pitjors], flush=True)
OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1))
