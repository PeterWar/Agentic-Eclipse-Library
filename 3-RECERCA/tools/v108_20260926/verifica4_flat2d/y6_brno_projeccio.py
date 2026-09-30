"""y6 (verificador adversari 4; còpia del x4 del verificador 3 amb la v4) · DETALL: el que la v3 treu del compost, és corona o patró? Brno com a jutge, amb dues mesures per banda i anell:
  r = correlació del DoG del ln (compost/base) amb el DoG del ln de Brno (mitjana RGB de L230, L231, L232 de l'estat de control);
  a = ⟨I, B⟩/⟨B, B⟩ = l'AMPLITUD de la part del compost que va amb Brno (la corona). Si la v3 treu corona, a baixa; si només treu patró o soroll,
      a queda igual i r puja. NUL: Brno desplaçat (41, −27) i (−97, 63) px.
  També E_resta = energia del compost que NO va amb Brno (I − a·B): el patró/soroll que es treu.
Bandes σ1–8, σ2–16, σ4–40; anells 1,02–1,5 … 6–10 R☉ (on Brno té senyal). compost i base: control, v2, v3.
Sortida: 4-RESULTATS/v108_20260926/verifica4_flat2d/Y6_BRNO_PROJECCIO.json"""
import json
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica4_flat2d'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'; CAD = A / '4-RESULTATS/v108_20260926/cadena'
IM = {'compost': {'control': F2 / 'compost_control.npy', 'v2': F2 / 'compost_flat2d_v2.npy', 'v3': F3 / 'compost_flat2d_v3.npy', 'v4': A / '4-RESULTATS/v108_20260926/flat2d_v4/compost_flat2d_v4.npy'},
      'base': {'control': CAD / 'control/lineal/base_G.npy', 'v2': CAD / 'flat2d_v2/lineal/base_G.npy', 'v3': CAD / 'flat2d_v3/lineal/base_G.npy', 'v4': CAD / 'flat2d_v4/lineal/base_G.npy'}}
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL; del yy, xx
def lnm(img):
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32), m
bb = sum(np.asarray(np.load(CAD / f'control/estat_v108/L{c}_RGB.npy', mmap_mode='r'), np.float32).mean(-1) for c in (230, 231, 232)) / 3
lb, mb = lnm(bb); del bb
BANDES = [(1, 8), (2, 16), (4, 40)]; ANELLS = [(1.02, 1.5), (1.5, 2.5), (2.5, 4), (4, 6), (6, 10)]
R = {}
for nom, ps in IM.items():
    L = {}; m = mb.copy()
    for v, p in ps.items():
        L[v], mi = lnm(np.asarray(np.load(p, mmap_mode='r'), np.float32)); m *= mi
    ng = lambda l, s: cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
    res = {}
    for s1, s2 in BANDES:
        er = int(2 * s2) | 1; ok = (cv2.erode(m, np.ones((er, er), np.uint8)) > 0) & (DL > 3); ok[::2] = False
        db = (ng(lb, s1) - ng(lb, s2)).astype(np.float32); dbs = [np.roll(np.roll(db, 41, 1), -27, 0), np.roll(np.roll(db, -97, 1), 63, 0)]
        D = {v: (ng(L[v], s1) - ng(L[v], s2)).astype(np.float32) for v in L}
        ob = {}
        for r0, r1 in ANELLS:
            k = ok & (RS >= r0) & (RS < r1)
            if k.sum() < 3000: continue
            b = db[k].astype(np.float64); b -= b.mean(); bbn = (b * b).sum(); o = {}
            for v in D:
                i = D[v][k].astype(np.float64); i -= i.mean()
                a = float((i * b).sum() / bbn); r = float((i * b).sum() / np.sqrt(bbn * (i * i).sum())); resta = i - a * b
                nul = [float(np.corrcoef(x[k], D[v][k])[0, 1]) for x in dbs]
                o[v] = dict(r=round(r, 4), a=round(a, 4), E_resta_ppm2=round(1e8 * float((resta ** 2).mean()), 2), E_total_ppm2=round(1e8 * float((i * i).mean()), 2), r_nuls=[round(x, 4) for x in nul])
            for v in ('v2', 'v3', 'v4'):
                o[v]['a_sobre_control'] = round(o[v]['a'] / o['control']['a'], 4) if o['control']['a'] != 0 else None
                o[v]['E_resta_sobre_control'] = round(o[v]['E_resta_ppm2'] / o['control']['E_resta_ppm2'], 4)
            ob[f'{r0}-{r1}'] = o
        res[f'{s1}-{s2}'] = ob; print(nom, s1, s2, json.dumps(ob), flush=True); del D, db, dbs
    R[nom] = res; del L
(OUT / 'Y6_BRNO_PROJECCIO.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
