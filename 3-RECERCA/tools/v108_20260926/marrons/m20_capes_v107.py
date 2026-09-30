"""m20 · QUINA CAPA porta cada traç a la V107: compost com el Photoshop (jutge_comu.comp; sense les capes d'ajust 239–244) de les capes
VISIBLES sota la 234 amb els ràsters de l'estat V105 (idèntics a la V107) i les MÀSCARES, ALFES, MODES i OPACITATS llegides de la V107
(la 41 i la 56 amb màscara retocada; la 54 MGN ara en Multiplicar 13/255). Per a cada traç (marca de Pere, ±60 px/±1,5°): solc fi del
compost sencer i del compost SENSE cada capa (la contribució de la capa = la diferència), en una caixa al voltant del traç.
Sortida: M20_CAPES_V107.json."""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924')); from jutge_comu import comp
ES = ARREL / '4-RESULTATS/v105_limbe_20260926/claude/estat_v105'; p = PSB(str(ARREL / '1-PHOTOSHOP/V107.psb'))
ordre = [l['id'] for l in p.layers]; vis = [l for l in p.layers if l['visible'] and l['id'] in (3, 54, 41, 42, 47, 49, 51, 45, 46, 55, 56)]
print('capes visibles (de baix a dalt):', [(l['id'], l['blend'], l['opacity']) for l in vis], flush=True)
MASC = {}
for l in vis:
    mk = p.channel_box(l['id'], -2, (0, 0, W, H), fill=(255 * 257 if (l['mask'] or {}).get('background') == 255 else 0)) if -2 in l['chans'] and l['mask'] and not l['mask']['disabled'] else None
    al = p.channel_box(l['id'], -1, (0, 0, W, H)) if -1 in l['chans'] else None
    MASC[l['id']] = (mk, al); print('llegida', l['id'], flush=True)
MODE = {'NORMAL': 'NORMAL', 'MULTIPLY': 'MULTIPLY', 'OVERLAY': 'OVERLAY', 'DIFFERENCE': 'DIFFERENCE'}
TH = np.arange(-1.5, 1.501, 0.25); TT = np.arange(-60, 61, 2.0)
def solc(img, org, tr):
    m = np.isfinite(img) & (img > 0); w = m.astype(np.float32); x = np.where(m, img, 0)
    ng = lambda a, s: cv2.GaussianBlur(a * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
    r = np.where(cv2.erode(w, np.ones((81, 81), np.uint8)) > 0, ng(x, 4) / np.maximum(ng(x, 40), 1e-12) - 1, np.nan).astype(np.float32)
    best = np.inf; c, d, L = tr['centre'], tr['d'], tr['llarg']
    for dth in TH:
        a = np.radians(dth); dd = np.array([d[0] * np.cos(a) - d[1] * np.sin(a), d[0] * np.sin(a) + d[1] * np.cos(a)]); nn = np.array([-dd[1], dd[0]])
        s = np.arange(-L / 2, L / 2 + 1e-6, 3.0)
        X = (c[0] + s[:, None] * dd[0] + TT[None, :] * nn[0]).astype(np.float32); Y = (c[1] + s[:, None] * dd[1] + TT[None, :] * nn[1]).astype(np.float32)
        P = mostreja(r, X, Y, org); cov = np.isfinite(P).mean(0)
        with np.errstate(all='ignore'): v = np.where(cov > 0.8, np.nanmean(P, 0), np.inf)
        best = min(best, float(np.min(v)))
    return best
res = {}
for tr in TRACOS:
    x0, y0, x1, y1 = caixa(tr, 400); box = (x0, y0, x1, y1); h, w = y1 - y0, x1 - x0; capes = []
    for l in vis:
        lid = l['id']; f = ES / (f'L{lid}_G.npy' if lid != 3 else 'L3_RGB.npy'); F = np.asarray(np.load(f, mmap_mode='r')[y0:y1, x0:x1], np.float32) / 65535
        mk, al = MASC[lid]; a = np.ones((h, w), np.float32)
        if al is not None: a *= al[y0:y1, x0:x1].astype(np.float32) / 65535
        if mk is not None: a *= mk[y0:y1, x0:x1].astype(np.float32) / 65535
        capes.append((lid, MODE[l['blend']], F, a * l['opacity'] / 255))
    def compost(sense=None):
        C, _ = comp([(md, F, a) for lid, md, F, a in capes if lid != sense], h, w); return C.mean(-1)
    tot = solc(compost(), (x0, y0), tr); fila = {'compost_sense_ajustos': tot}
    for lid, *_ in capes:
        if lid == 3: continue
        v = solc(compost(sense=lid), (x0, y0), tr); fila[f'sense_{lid}'] = v; fila[f'contribucio_{lid}'] = tot - v
    fila['nomes_base_3'] = solc(capes[[c[0] for c in capes].index(3)][2].mean(-1), (x0, y0), tr)
    res[tr['k']] = fila
    print(f"T{tr['k']} compost {tot*1e4:+.0f}‱ | " + ' '.join(f"{k.split('_')[1]}:{v*1e4:+.0f}" for k, v in fila.items() if k.startswith('contribucio')) + f" | base sola {fila['nomes_base_3']*1e4:+.1f}‱", flush=True)
desa(OUT / 'M20_CAPES_V107.json', dict(capes_visibles=[(l['id'], l['name'], l['blend'], l['opacity']) for l in vis], nota='contribució = solc(compost) − solc(compost sense la capa), en ‱ del contrast fi σ4/40; negatiu = la capa fa el traç més fosc', tracos=res))
