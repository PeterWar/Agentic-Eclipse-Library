"""y2 (verificador adversari 4) · TAQUES NOVES I TAQUES PASSADES amb el cel anul·lat, criteri propi (no el del verificador 3 ni el m2 de l'autor).
Sony: Z_v = ln A_v − ln B_v; Vixen: Z_v = ln V_v − S (S = Sony A+B del CONTROL, fixa). v = control, v3, v4.
Banda σ6 − σ36 (la del verificador 3 era 10–60). σ robusta (MAD) de Z_control per anells de 0,5 R☉. Màxims locals |z| (finestra 101 px), R > 1,6 R☉.
  · NOVES respecte del control: taca de v a |z| ≥ 3,5 sense cap píxel del control a ≤ 30 px amb el mateix signe i |z| ≥ 1,5 (més estricte amb v).
  · NOVES respecte de la v3: el mateix, però la referència és la v3 (el que la v4 crea de nou).
  · PASSADES: als màxims del control (|z| ≥ 3,5), la v4 hi deixa el signe girat amb |z| ≥ 2,5 (sobrecorrecció). Comptatge v3 i v4.
  · Els màxims del control dins de les petjades de la v4 (canvi v4 − v3): residu mitjà ponderat Σ Z_v·Z_c / Σ Z_c² per a control, v3 i v4.
  · Energia a la banda, v/control, fora i dins de les petjades.
Sortida: 4-RESULTATS/v108_20260926/verifica4_flat2d/Y2_TAQUES.json (només lectura; ~10 GB)."""
import json, time
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica4_flat2d'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603
CR = A / '4-RESULTATS/v97_refundacio_20260924'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'; F4 = A / '4-RESULTATS/v108_20260926/flat2d_v4'
AP = {'control': dict(V=CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', A=CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', B=CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy'),
      'v3': dict(V=F3 / 'apilats/vixen_total.npy', A=F3 / 'apilats/sony_A_total.npy', B=F3 / 'apilats/cau/sony_B_total_v42.npy'),
      'v4': dict(V=F4 / 'apilats/vixen_total.npy', A=F4 / 'apilats/sony_A_total.npy', B=F4 / 'apilats/cau/sony_B_total_v42.npy')}
t0 = time.time()
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; del yy, xx
def lnG(p):
    x = np.asarray(np.load(p, mmap_mode='r')[..., 1], np.float32); ok = np.isfinite(x) & (x > 0)
    return np.where(ok, np.log(np.maximum(x, 1e-20)), 0).astype(np.float32), ok
R = {}
for tz in ('sony', 'vixen'):
    Z = {}; okz = None
    if tz == 'vixen':
        a, oa = lnG(AP['control']['A']); b, ob = lnG(AP['control']['B']); S = np.where(oa & ob, 0.5 * (a + b), np.where(oa, a, b)).astype(np.float32); oS = oa | ob; del a, b
    for v in AP:
        if tz == 'sony':
            a, oa = lnG(AP[v]['A']); b, ob = lnG(AP[v]['B']); o = oa & ob; z = a - b; del a, b
        else:
            a, oa = lnG(AP[v]['V']); o = oa & oS; z = a - S; del a
        Z[v] = np.where(o, z, 0).astype(np.float32); okz = o if okz is None else okz & o
    if tz == 'vixen': del S
    # petjades de la v4 (canvi v4 − v3 a l'apilat de cada tren)
    pet = np.zeros((H, W), bool)
    for k_ in (('A', 'B') if tz == 'sony' else ('V',)):
        d3, _ = lnG(AP['v3'][k_]); d4, _ = lnG(AP['v4'][k_]); pet |= np.abs(cv2.GaussianBlur(d4 - d3, (0, 0), 3)) > 5e-5; del d3, d4
    pet = cv2.dilate(pet.astype(np.uint8), np.ones((31, 31), np.uint8)) > 0
    m = okz.astype(np.float32); okb = (cv2.erode(m, np.ones((241, 241), np.uint8)) > 0) & (RS > 1.6)
    ng = lambda x, s: cv2.GaussianBlur(x * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
    D = {v: np.where(okb, ng(Z[v], 6) - ng(Z[v], 36), 0).astype(np.float32) for v in Z}; del Z
    sig = np.zeros((H, W), np.float32)
    for r0 in np.arange(1.5, 25, 0.5):
        k = okb & (RS >= r0) & (RS < r0 + 0.5)
        if k.sum() < 5000: continue
        x = D['control'][k][::5]; sig[k] = 1.4826 * float(np.median(np.abs(x - np.median(x))))
    zz = {v: np.where(sig > 0, D[v] / np.maximum(sig, 1e-12), 0).astype(np.float32) for v in D}
    def pics(z, th):
        az = np.abs(z); mx = cv2.dilate(az, np.ones((101, 101), np.uint8)); pk = okb & (sig > 0) & (az == mx) & (az >= th); ys, xs = np.nonzero(pk)
        return list(zip(xs.tolist(), ys.tolist(), z[ys, xs].tolist()))
    def te(zr, x, y, s, rad=30, th=1.5):
        w = zr[max(0, y - rad):y + rad + 1, max(0, x - rad):x + rad + 1]; return bool(((np.sign(w) == np.sign(s)) & (np.abs(w) >= th)).any())
    o = {}
    for th in (3.5, 4.0):
        pc = pics(zz['control'], th); o[f'n_pics_control_z{th}'] = len(pc)
        for v in ('v3', 'v4'):
            pv = pics(zz[v], th); nov_c = [(x, y, s) for x, y, s in pv if not te(zz['control'], x, y, s)]
            q = dict(n=len(pv), noves_vs_control=len(nov_c), noves_vs_control_dins_petjades_v4=int(sum(pet[y, x] for x, y, _ in nov_c)),
                     llista_noves=[dict(x=x, y=y, z=round(s, 2), z_control=round(float(zz['control'][y, x]), 2), z_v3=round(float(zz['v3'][y, x]), 2), R=round(float(RS[y, x]), 2), dins_petjada=bool(pet[y, x]))
                                   for x, y, s in sorted(nov_c, key=lambda t: -abs(t[2]))[:15]])
            if v == 'v4':
                nov_3 = [(x, y, s) for x, y, s in pv if not te(zz['v3'], x, y, s)]
                q['noves_vs_v3'] = len(nov_3); q['llista_noves_vs_v3'] = [dict(x=x, y=y, z=round(s, 2), z_v3=round(float(zz['v3'][y, x]), 2), z_control=round(float(zz['control'][y, x]), 2),
                                                                             R=round(float(RS[y, x]), 2), dins_petjada=bool(pet[y, x])) for x, y, s in sorted(nov_3, key=lambda t: -abs(t[2]))[:15]]
            pas = [(x, y, s) for x, y, s in pc if np.sign(zz[v][y, x]) == -np.sign(s) and abs(zz[v][y, x]) >= 2.5]
            q['passades_z2.5'] = len(pas); q['llista_passades'] = [dict(x=x, y=y, z_control=round(s, 2), z_v=round(float(zz[v][y, x]), 2), dins_petjada=bool(pet[y, x])) for x, y, s in pas[:15]]
            o[f'{v}_z{th}'] = q
        dins = [(x, y) for x, y, _ in pc if pet[y, x]]; o[f'pics_control_dins_petjades_z{th}'] = len(dins)
        if dins:
            den = sum(float(D['control'][y, x]) ** 2 for x, y in dins)
            o[f'residu_pics_dins_petjades_z{th}'] = {v: round(sum(float(D[v][y, x] * D['control'][y, x]) for x, y in dins) / den, 3) for v in ('v3', 'v4')}
            o[f'intactes_dins_petjades_z{th}'] = {v: int(sum(D[v][y, x] / D['control'][y, x] > 0.8 for x, y in dins)) for v in ('v3', 'v4')}
        tot = pc; den = sum(float(D['control'][y, x]) ** 2 for x, y, _ in tot)
        o[f'residu_pics_control_tots_z{th}'] = {v: round(sum(float(D[v][y, x] * D['control'][y, x]) for x, y, _ in tot) / den, 3) for v in ('v3', 'v4')}
        o[f'intactes_tots_z{th}'] = {v: int(sum(D[v][y, x] / D['control'][y, x] > 0.8 for x, y, _ in tot)) for v in ('v3', 'v4')}
    for nom, sel in (('fora_petjades', okb & ~pet), ('dins_petjades', okb & pet)):
        e0 = float((D['control'][sel].astype(np.float64) ** 2).sum()); o[f'energia_banda_{nom}'] = {v: round(float((D[v][sel].astype(np.float64) ** 2).sum()) / e0, 4) for v in ('v3', 'v4')}
    R[tz] = o; print(tz, json.dumps({k: v for k, v in o.items() if 'llista' not in str(k)}, default=str)[:3000], f'{time.time()-t0:.0f}s', flush=True)
    del D, zz, sig, pet
    (OUT / 'Y2_TAQUES.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
print('FET')
