"""x3 (verificador adversari 3) · PROVA PRÒPIA AMB EL CEL ANUL·LAT del canvi SENCER de la v3 (i de la v2, per comparar).
Sony: Z = ln A_control − ln B_control (el cel s'anul·la; només hi queda el que va fix al sensor), U_v = (ln A_v − ln A_control) − (ln B_v − ln B_control).
Vixen: Z = ln V_control − ln S_control (S = mitjana de ln A i ln B de la Sony, del control), U_v = ln V_v − ln V_control.
β = ⟨Z,U⟩/⟨U,U⟩ per banda (DoG en px del llenç), anell (R☉) i, a la Sony, per distància a la vora del camp comú A∩B (px).
β = −1: el canvi treu un defecte que hi era sencer (cura); β = 0: no hi era (injecció); s = 1 + 2β (s ≤ 0 = cura neta).
NUL: la mateixa β amb U desplaçat (12 desplaçaments 150–600 px) → σ_nul; z = β/σ_nul. Escrit independentment del d2 de l'autor.
Quantitats: ln G, ln R/G, ln B/G (a l'espai dels apilats, abans de la matriu).
Ús: x3_prova_cel_anullat.py sony|vixen   Sortida: 4-RESULTATS/v108_20260926/verifica3_flat2d/X3_<tren>.json"""
import json, sys
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica3_flat2d'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
CR = A / '4-RESULTATS/v97_refundacio_20260924'; F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'
AP = {'control': dict(V=CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', A=CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', B=CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy'),
      'v2': dict(V=F2 / 'apilats/vixen_total.npy', A=F2 / 'apilats/sony_A_total.npy', B=F2 / 'apilats/cau/sony_B_total_v42.npy'),
      'v3': dict(V=F3 / 'apilats/vixen_total.npy', A=F3 / 'apilats/sony_A_total.npy', B=F3 / 'apilats/cau/sony_B_total_v42.npy')}
tren = (sys.argv[1:] or ['sony'])[0]
def q(p, nom):
    x = np.load(p, mmap_mode='r'); G = np.asarray(x[..., 1], np.float32)
    v = G if nom == 'lnG' else np.asarray(x[..., 0 if nom == 'lnRG' else 2], np.float32) / np.maximum(G, 1e-20)
    ok = np.isfinite(v) & (v > 0) & np.isfinite(G) & (G > 0)
    return np.where(ok, np.log(np.maximum(v, 1e-20)), 0).astype(np.float32), ok
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL
SUB = ((yy.astype(np.int32) % 2) == 0) & ((xx.astype(np.int32) % 2) == 0); del yy, xx
BANDES = [(2, 6), (6, 18), (18, 54), (54, 160)]; ANELLS = [(1.5, 3), (3, 6), (6, 10), (10, 30)]
rng = np.random.default_rng(3); DESPL = []
while len(DESPL) < 12:
    r = rng.uniform(150, 600); t = rng.uniform(0, 2 * np.pi); DESPL.append((int(r * np.cos(t)), int(r * np.sin(t))))
VORES = [(0, 400), (400, 1200), (1200, 99999)]
R = dict(tren=tren, bandes=BANDES, anells=ANELLS, despl=DESPL, q={})
for nom in ('lnG', 'lnRG', 'lnBG'):
    if tren == 'sony':
        XA, oA = q(AP['control']['A'], nom); XB, oB = q(AP['control']['B'], nom); ok = oA & oB
        Z0 = np.where(ok, XA - XB, 0).astype(np.float32); U0 = {}
        for v in ('v2', 'v3'):
            ya, a1 = q(AP[v]['A'], nom); yb, b1 = q(AP[v]['B'], nom); ok &= a1 & b1
            U0[v] = ((ya - XA) - (yb - XB)).astype(np.float32); del ya, yb
        del XA, XB
    else:
        XV, oV = q(AP['control']['V'], nom); XA, oA = q(AP['control']['A'], nom); XB, oB = q(AP['control']['B'], nom)
        S = np.where(oA & oB, 0.5 * (XA + XB), np.where(oA, XA, XB)).astype(np.float32); ok = oV & (oA | oB); del XA, XB
        Z0 = np.where(ok, XV - S, 0).astype(np.float32); del S; U0 = {}
        for v in ('v2', 'v3'):
            yv, v1 = q(AP[v]['V'], nom); ok &= v1; U0[v] = (yv - XV).astype(np.float32); del yv
        del XV
    ok &= (DL > 80) & (RS > 1.2); m = ok.astype(np.float32)
    DV = cv2.distanceTransform((m > 0).astype(np.uint8), cv2.DIST_L2, 5)
    Z0 *= m
    for v in U0: U0[v] *= m
    ng = lambda x, s: cv2.GaussianBlur(x, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
    out = {}
    for s1, s2 in BANDES:
        er = int(2 * s2) | 1; okb = cv2.erode(m, np.ones((er, er), np.uint8)) > 0
        Z = (ng(Z0, s1) - ng(Z0, s2)).astype(np.float32); U = {v: (ng(U0[v], s1) - ng(U0[v], s2)).astype(np.float32) for v in U0}
        ob = {}
        def mesura(k):
            o = {}
            for v in U:
                u = U[v][k].astype(np.float64); z = Z[k].astype(np.float64); uu = (u * u).sum()
                if uu <= 0: continue
                b = float((z * u).sum() / uu); nb = []
                for dx, dy in DESPL:
                    ks = k & np.roll(np.roll(okb, dx, 1), dy, 0); us = np.roll(np.roll(U[v], dx, 1), dy, 0)[ks].astype(np.float64)
                    nb.append(float((Z[ks].astype(np.float64) * us).sum() / max((us * us).sum(), 1e-30)))
                sd = float(np.sqrt(np.mean(np.square(nb))))
                o[v] = dict(beta=round(b, 3), sd_nul=round(sd, 3), z=round(b / sd, 1) if sd > 0 else None, s=round(1 + 2 * b, 2),
                            rms_U_ppm=round(1e4 * float(np.sqrt(uu / k.sum())), 2), rms_Z_ppm=round(1e4 * float(np.sqrt((z * z).mean())), 2))
            return o
        for r0, r1 in ANELLS:
            k = okb & SUB & (RS >= r0) & (RS < r1)
            if k.sum() < 20000: continue
            ob[f'{r0}-{r1}'] = mesura(k)
        if tren == 'sony':
            for d0, d1 in VORES:
                k = okb & SUB & (RS >= 3) & (DV >= d0) & (DV < d1)
                if k.sum() < 20000: continue
                ob[f'vora_{d0}-{d1}px_Rsol>3'] = mesura(k)
        out[f'{s1}-{s2}px'] = ob; print(tren, nom, s1, s2, json.dumps(ob), flush=True)
        del Z, U
    R['q'][nom] = out; del Z0, U0
    (OUT / f'X3_{tren}.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
