"""y3 (verificador adversari 4) · ELS 2 PÍXELS DE LA PROTUBERÀNCIA I LA CAUSA ARREL A LA FRANJA.
1) Als 2 píxels: base_G, compost i la franja (G, domini_E, E) de control, v3 i v4.
2) Domini: domini_E de la v4 == control? Quants píxels de la franja de la v4 són del control i no de la variant (G i F idèntics al control
   on la variant hauria de diferir)?
3) CAUSA ARREL: la fragilitat era G' post-matriu ≈ 0 (E_G petit davant E_R). Si la regla només tapa els píxels que CANVIEN DE DOMINI, els que
   són al domini amb G' igual de petit poden saltar igual. Mesura: dins del domini de la franja, r = ln(base_v/base_control) per a v3 i v4,
   separat per la fragilitat f = |E_G| / (|E_R| + |E_G| + |E_B|) del control (f < 0,002, 0,002–0,01, > 0,01), i els píxels amb |r| > 0,15.
   El mateix al compost. Nul: la mateixa estadística a la corona del voltant (fora de la franja, 30–120 px del limbe), on el flat canvia igual.
Sortida: 4-RESULTATS/v108_20260926/verifica4_flat2d/Y3_PROTUBERANCIA.json (només lectura; < 3 GB)."""
import json
from pathlib import Path
import numpy as np
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica4_flat2d'; CAD = A / '4-RESULTATS/v108_20260926/cadena'
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'; F4 = A / '4-RESULTATS/v108_20260926/flat2d_v4'
LLUNA = (5375.787, 3775.977); RL = 452.98
V = {'control': 'control', 'v3': 'flat2d_v3', 'v4': 'flat2d_v4'}
CMP = {'control': F2 / 'compost_control.npy', 'v3': F3 / 'compost_flat2d_v3.npy', 'v4': F4 / 'compost_flat2d_v4.npy'}
FR = {v: np.load(CAD / d / 'franja/A3C_franja_silueta.npz') for v, d in V.items()}
by0, by1, bx0, bx1 = [int(x) for x in FR['control']['box']]
BG = {v: np.asarray(np.load(CAD / d / 'lineal/base_G.npy', mmap_mode='r')[by0:by1, bx0:bx1], np.float64) for v, d in V.items()}
CP = {v: np.asarray(np.load(p, mmap_mode='r')[by0:by1, bx0:bx1], np.float64) for v, p in CMP.items()}
R = {'box': [by0, by1, bx0, bx1]}
PX = [(4905, 3779), (4897, 3785), (4897, 3786), (4906, 3779), (4904, 3779), (4905, 3778), (4905, 3780), (4898, 3785), (4896, 3785)]
R['pixels'] = []
for x, y in PX:
    yy, xx = y - by0, x - bx0; e = dict(x=x, y=y)
    for v in V:
        f = FR[v]; e[v] = dict(base_G=round(float(BG[v][yy, xx]), 1), compost=round(float(CP[v][yy, xx]), 5), franja_G=round(float(f['G'][yy, xx]), 1), domini_E=bool(f['domini_E'][yy, xx]),
                               E=[round(float(t), 1) for t in f['E'][yy, xx]], beta=round(float(f['beta'][yy, xx]), 3))
    R['pixels'].append(e)
C = FR['control']; F = FR['v4']; F3_ = FR['v3']
R['domini_E_v4_igual_control'] = bool(np.array_equal(F['domini_E'], C['domini_E'])); R['domini_E_v3_px_diferents_control'] = int((F3_['domini_E'] != C['domini_E']).sum())
R['px_franja_G_v4_identics_control_dins_domini'] = int(((F['G'] == C['G']) & C['domini_E']).sum()); R['px_franja_G_v3_identics_control_dins_domini'] = int(((F3_['G'] == C['G']) & C['domini_E']).sum())
R['px_domini_E_control'] = int(C['domini_E'].sum())
yy, xx = np.mgrid[by0:by1, bx0:bx1]; dL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL
E = C['E'].astype(np.float64); fr = np.abs(E[..., 1]) / np.maximum(np.abs(E).sum(-1), 1e-9)
dom = C['domini_E']; ok = dom & np.isfinite(fr)
for v in ('v3', 'v4'):
    for nom, X in (('base_G', BG), ('compost', CP)):
        valid = (X['control'] > 0) & (X[v] > 0); r = np.where(valid, np.log(np.maximum(X[v], 1e-12) / np.maximum(X['control'], 1e-12)), np.nan)
        o = {}
        for lab, sel in (('f<0.002', ok & (fr < 0.002)), ('f0.002-0.01', ok & (fr >= 0.002) & (fr < 0.01)), ('f>0.01', ok & (fr >= 0.01)),
                         ('nul_corona_30-120px_fora_domini', ~dom & (dL > 30) & (dL < 120))):
            rr = r[sel & valid]
            if rr.size == 0: o[lab] = None; continue
            o[lab] = dict(n=int(rr.size), p50_abs=round(float(np.median(np.abs(rr))), 5), p99_abs=round(float(np.percentile(np.abs(rr), 99)), 4), max_abs=round(float(np.abs(rr).max()), 4),
                          n_abs_mes_0_15=int((np.abs(rr) > 0.15).sum()), n_abs_mes_0_5=int((np.abs(rr) > 0.5).sum()))
        k = ok & valid & (np.abs(r) > 0.15); ys, xs = np.nonzero(k); ordre = np.argsort(-np.abs(r[ys, xs]))[:15]
        o['pitjors_domini'] = [dict(x=int(xs[i] + bx0), y=int(ys[i] + by0), r=round(float(r[ys[i], xs[i]]), 3), f=round(float(fr[ys[i], xs[i]]), 5), dL=round(float(dL[ys[i], xs[i]]), 1),
                                    control=round(float(X['control'][ys[i], xs[i]]), 4), v=round(float(X[v][ys[i], xs[i]]), 4)) for i in ordre]
        R[f'{nom}_{v}_sobre_control'] = o
        print(v, nom, json.dumps({kk: vv for kk, vv in o.items() if kk != 'pitjors_domini'}), flush=True)
(OUT / 'Y3_PROTUBERANCIA.json').write_text(json.dumps(R, ensure_ascii=False, indent=1)); print(json.dumps(R['pixels'][:3], indent=0)); print('FET')
