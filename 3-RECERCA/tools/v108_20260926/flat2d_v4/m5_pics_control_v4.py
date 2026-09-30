"""m5_pics_control_v4 (V108, flat2d_v4) · ELS 81 PICS DEL CONTROL (Sony, A − B, |z| ≥ 4 a la banda de la pols σ10–60; m2 / x6 del verificador 3):
per què la v3 en deixa 42 intactes i la v2 31, i què hi fa la v4. Per a cada pic: el residu Z_v/Z_control de v2, v3 i v4, i si la v4 hi toca
(|Δ_v4 − Δ_v3| a Z > 1 ‱: el pic cau dins d'una petjada que la v3 rebutjava) o no. Si els pics que la v2 curava i la v3 no, NO són dins de
cap petjada rebutjada, el que la v2 hi posava de més venia de la part de C que no és de taca (la cromàtica que la dada no sosté, §1 de la v3),
i la porta per grup no els pot curar.
Sortida: 4-RESULTATS/v108_20260926/flat2d_v4/M5_PICS_CONTROL.json   (només lectura; ~8 GB)"""
import json
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/flat2d_v4'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603
CR = A / '4-RESULTATS/v97_refundacio_20260924'; F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'
AP = {'control': (CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy'),
      'v2': (F2 / 'apilats/sony_A_total.npy', F2 / 'apilats/cau/sony_B_total_v42.npy'), 'v3': (F3 / 'apilats/sony_A_total.npy', F3 / 'apilats/cau/sony_B_total_v42.npy'),
      'v4': (OUT / 'apilats/sony_A_total.npy', OUT / 'apilats/cau/sony_B_total_v42.npy')}
def lnG(p):
    x = np.asarray(np.load(p, mmap_mode='r')[..., 1], np.float32); ok = np.isfinite(x) & (x > 0)
    return np.where(ok, np.log(np.maximum(x, 1e-20)), 0).astype(np.float32), ok
M2 = json.loads((OUT / 'M2_TAQUES_FORATS.json').read_text())['sony']['pics_control_z4_llista']
Z = {}; ok = None
for v, (pa, pb) in AP.items():
    a, oa = lnG(pa); b, ob = lnG(pb); Z[v] = (a - b).astype(np.float32); o = oa & ob; ok = o if ok is None else ok & o; del a, b
m = ok.astype(np.float32); ng = lambda x, s: cv2.GaussianBlur(x * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
D = {v: (ng(Z[v], 10) - ng(Z[v], 60)).astype(np.float32) for v in Z}; del Z
llista = []
for p in M2:
    x, y = p['x'], p['y']; z0 = float(D['control'][y, x])
    r = {v: float(D[v][y, x] / z0) for v in ('v2', 'v3', 'v4')}; t4 = abs(float(D['v4'][y, x] - D['v3'][y, x])) * 1e4
    llista.append(dict(x=x, y=y, z=p['z'], R_sol=round(float(np.hypot(x - SOL[0], y - SOL[1]) / RSOL), 2), Z_control_ppm=round(1e4 * z0, 1),
                       residu={v: round(q, 3) for v, q in r.items()}, v4_hi_toca=bool(t4 > 1.0), canvi_v4_menys_v3_ppm=round(t4, 2)))
def n(f): return int(sum(1 for e in llista if f(e)))
res = dict(n_pics=len(llista),
           intactes_mes_0_8={v: n(lambda e, v=v: e['residu'][v] > 0.8) for v in ('v2', 'v3', 'v4')},
           v2_cura_i_v3_no=n(lambda e: e['residu']['v2'] <= 0.8 < e['residu']['v3']),
           v2_cura_i_v3_no__dins_petjada_v4=n(lambda e: e['residu']['v2'] <= 0.8 < e['residu']['v3'] and e['v4_hi_toca']),
           pics_on_la_v4_hi_toca=n(lambda e: e['v4_hi_toca']),
           d_residu_v4_menys_v3_on_hi_toca=[round(e['residu']['v4'] - e['residu']['v3'], 3) for e in llista if e['v4_hi_toca']], pics=llista)
(OUT / 'M5_PICS_CONTROL.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
print(json.dumps({k: v for k, v in res.items() if k != 'pics'}, ensure_ascii=False))
