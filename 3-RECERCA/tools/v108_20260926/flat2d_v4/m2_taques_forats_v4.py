"""m2_taques_forats_v4 (V108, flat2d_v4) · LES PROVES DEL VERIFICADOR 3 (x6_taques_cel_anullat.py, copiat i ampliat) per a la v4, amb la v3 al costat.
TAQUES (A): amb el cel ANUL·LAT. Sony: Z_v = ln A_v − ln B_v (G). Vixen: Z_v = ln V_v − S (S = mitjana de ln A i ln B de la Sony del control, fixa).
  Banda de pols DoG σ10 − σ60; σ robusta (MAD) de Z_control per anells d'1 R☉; màxims locals |z| (finestra 121 px), a R > 1,6 R☉, vora ≥ 150 px.
  · taques amb |z| ≥ 3 i ≥ 4 a cada versió; NOVES = sense cap taca del control a ≤ 40 px amb el mateix signe i |z| ≥ 2 (el criteri del verificador).
  · als pics del control (|z| ≥ 4): residu Z_v/Z_control (0 = curat, 1 = intacte, < 0 = passat); quants queden intactes (> 0,8) i quants curats (< 0,2).
  · energia a la banda de la pols, v/control.
FORATS (B), al compost (màscares de la V107): energia σ1–4 i σ4–40 de v/control DINS de cada zona contra un anell de 60–200 px al voltant.
  Zones: (1) els forats del verificador (a l'apilat, la v3 no toca res, |Δ_v3| σ3 < 2·10⁻⁶, i la v2 sí, |Δ_v2| σ3 > 3·10⁻⁴: la C sencera no aplicada);
  (2) les petjades que la v4 canvia respecte de la v3 (|Δ_v4 − Δ_v3| σ3 > 1·10⁻⁴ a l'apilat). «Com el voltant» = contrast dins/anell ≈ 1.
Ús: m2_taques_forats_v4.py [A] [B]   Sortida: 4-RESULTATS/v108_20260926/flat2d_v4/M2_TAQUES_FORATS.json   (només lectura; ~12 GB)"""
import json, sys
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/flat2d_v4'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603
CR = A / '4-RESULTATS/v97_refundacio_20260924'; F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'; F4 = OUT
AP = {'control': dict(V=CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', A=CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', B=CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy'),
      'v2': dict(V=F2 / 'apilats/vixen_total.npy', A=F2 / 'apilats/sony_A_total.npy', B=F2 / 'apilats/cau/sony_B_total_v42.npy'),
      'v3': dict(V=F3 / 'apilats/vixen_total.npy', A=F3 / 'apilats/sony_A_total.npy', B=F3 / 'apilats/cau/sony_B_total_v42.npy'),
      'v4': dict(V=F4 / 'apilats/vixen_total.npy', A=F4 / 'apilats/sony_A_total.npy', B=F4 / 'apilats/cau/sony_B_total_v42.npy')}
CMP = {'control': F2 / 'compost_control.npy', 'v3': F3 / 'compost_flat2d_v3.npy', 'v4': F4 / 'compost_flat2d_v4.npy'}
VERS = ('control', 'v3', 'v4')
quins = sys.argv[1:] or ['A', 'B']
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; del yy, xx
def lnG(p):
    x = np.asarray(np.load(p, mmap_mode='r')[..., 1], np.float32); ok = np.isfinite(x) & (x > 0)
    return np.where(ok, np.log(np.maximum(x, 1e-20)), 0).astype(np.float32), ok
pj = OUT / 'M2_TAQUES_FORATS.json'; R = json.loads(pj.read_text()) if pj.exists() else {}
def desa(): pj.write_text(json.dumps(R, ensure_ascii=False, indent=1))
if 'A' in quins:
    for tren in ('sony', 'vixen'):
        Z = {}; ok = None
        if tren == 'vixen':
            a, oa = lnG(AP['control']['A']); b, ob = lnG(AP['control']['B']); S = np.where(oa & ob, 0.5 * (a + b), np.where(oa, a, b)).astype(np.float32); oS = oa | ob; del a, b
        for v in VERS:
            if tren == 'sony':
                a, oa = lnG(AP[v]['A']); b, ob = lnG(AP[v]['B']); o = oa & ob; z = (a - b); del a, b
            else:
                a, oa = lnG(AP[v]['V']); o = oa & oS; z = a - S; del a
            Z[v] = np.where(o, z, 0).astype(np.float32); ok = o if ok is None else ok & o
        if tren == 'vixen': del S
        m = ok.astype(np.float32); okb = cv2.erode(m, np.ones((301, 301), np.uint8)) > 0; okb &= RS > 1.6
        ng = lambda x, s: cv2.GaussianBlur(x * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
        D = {v: np.where(okb, ng(Z[v], 10) - ng(Z[v], 60), 0).astype(np.float32) for v in Z}; del Z
        sig = np.zeros((H, W), np.float32)
        for r0 in range(1, 25):
            k = okb & (RS >= r0) & (RS < r0 + 1)
            if k.sum() < 5000: continue
            x = D['control'][k][::7]; sig[k] = 1.4826 * float(np.median(np.abs(x - np.median(x))))
        zz = {v: np.where(sig > 0, D[v] / np.maximum(sig, 1e-12), 0).astype(np.float32) for v in D}
        zc = zz['control']
        def te_control(x, y, s):
            y0, y1, x0, x1 = max(0, y - 40), y + 41, max(0, x - 40), x + 41; w = zc[y0:y1, x0:x1]
            return bool(((np.sign(w) == np.sign(s)) & (np.abs(w) >= 2)).any())
        o = {}; pics4 = {}
        for v in zz:
            az = np.abs(zz[v]); mx = cv2.dilate(az, np.ones((121, 121), np.uint8)); o[v] = {}
            for zl in (3, 4):
                pk = okb & (az == mx) & (az >= zl); ys, xs = np.nonzero(pk); pics = list(zip(xs.tolist(), ys.tolist(), zz[v][ys, xs].tolist()))
                if zl == 4: pics4[v] = pics
                noves = [dict(x=x, y=y, z=round(s, 2), z_control=round(float(zc[y, x]), 2), R_sol=round(float(RS[y, x]), 2)) for x, y, s in pics if not te_control(x, y, s)] if v != 'control' else []
                o[v][f'z{zl}'] = dict(n=len(pics), n_noves=len(noves), noves=sorted(noves, key=lambda t: -abs(t['z']))[:15])
            del az, mx
        cp = pics4['control']
        for v in ('v3', 'v4'):
            num = sum(D[v][y, x] * D['control'][y, x] for x, y, _ in cp); den = sum(D['control'][y, x] ** 2 for x, y, _ in cp)
            fr = np.array([float(D[v][y, x] / D['control'][y, x]) for x, y, _ in cp])
            o[v]['pics_control_z4'] = dict(n=len(cp), residu_ponderat=round(float(num / den), 3) if den > 0 else None, residu_mediana=round(float(np.median(fr)), 3) if len(fr) else None,
                                           n_intactes_residu_mes_0_8=int((fr > 0.8).sum()), n_curats_residu_menys_0_2=int((fr < 0.2).sum()), n_passats_residu_menys_0=int((fr < 0).sum()))
        o['pics_control_z4_llista'] = [dict(x=x, y=y, z=round(s, 2), residu_v3=round(float(D['v3'][y, x] / D['control'][y, x]), 3), residu_v4=round(float(D['v4'][y, x] / D['control'][y, x]), 3)) for x, y, s in cp]
        o['energia_banda_pols_sobre_control'] = {v: round(float((D[v][okb].astype(np.float64) ** 2).sum() / (D['control'][okb].astype(np.float64) ** 2).sum()), 4) for v in ('v3', 'v4')}
        R[tren] = o; print(tren, json.dumps({v: o[v] for v in VERS}), 'energia', o['energia_banda_pols_sobre_control'], flush=True); del D, zz, sig
        desa()
if 'B' in quins:
    cm = {}
    for v, p in CMP.items():
        x = np.asarray(np.load(p, mmap_mode='r'), np.float32); mm = (np.isfinite(x) & (x > 0)).astype(np.float32); l = np.where(mm > 0, np.log(np.maximum(x, 1e-12)), 0).astype(np.float32); del x
        g = lambda s: cv2.GaussianBlur(l * mm, (0, 0), s) / np.maximum(cv2.GaussianBlur(mm, (0, 0), s), 1e-6)
        g1 = g(1); g4 = g(4); cm[v] = dict(b14=((g1 - g4) ** 2).astype(np.float32), b440=((g4 - g(40)) ** 2).astype(np.float32)); del l, g1, g4
    def mesura(lab, st, n, ero):
        res = []
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < 3000: continue
            x0, y0, w, h = st[i, :4]; pad = 220; ya, yb, xa, xb = max(0, y0 - pad), min(H, y0 + h + pad), max(0, x0 - pad), min(W, x0 + w + pad)
            f = lab[ya:yb, xa:xb] == i; dist = cv2.distanceTransform((~f).astype(np.uint8), cv2.DIST_L2, 5); ring = (dist >= 60) & (dist < 200) & (lab[ya:yb, xa:xb] == 0) & ero[ya:yb, xa:xb]
            fin = cv2.erode(f.astype(np.uint8), np.ones((21, 21), np.uint8)) > 0
            if fin.sum() < 500 or ring.sum() < 2000: continue
            e = {}
            for b in ('b14', 'b440'):
                e[b] = {}
                for v in ('v3', 'v4'):
                    rin = cm[v][b][ya:yb, xa:xb][fin].mean() / cm['control'][b][ya:yb, xa:xb][fin].mean(); rout = cm[v][b][ya:yb, xa:xb][ring].mean() / cm['control'][b][ya:yb, xa:xb][ring].mean()
                    e[b][v] = dict(dins=round(float(rin), 3), anell=round(float(rout), 3), contrast_dins_sobre_anell=round(float(rin / rout), 3))
            res.append(dict(centre=[int(x0 + w / 2), int(y0 + h / 2)], area_px=int(st[i, cv2.CC_STAT_AREA]), R_sol=round(float(RS[int(y0 + h / 2), int(x0 + w / 2)]), 2), **e))
        return res
    def resum(res):
        if not res: return None
        o = {}
        for v in ('v3', 'v4'):
            c = np.array([r['b440'][v]['contrast_dins_sobre_anell'] for r in res])
            o[v] = dict(n=len(c), contrast_s4_40_p50=round(float(np.median(c)), 3), contrast_s4_40_max=round(float(c.max()), 3), contrast_s4_40_min=round(float(c.min()), 3),
                        n_mes_1_3=int((c > 1.3).sum()), n_menys_0_77=int((c < 0.77).sum()), rms_log=round(float(np.sqrt(np.mean(np.log(c) ** 2))), 3))
        return o
    for tren, k_ in (('sony_A', 'A'), ('sony_B', 'B'), ('vixen', 'V')):
        c, oc = lnG(AP['control'][k_]); d3, o3 = lnG(AP['v3'][k_]); d2, o2 = lnG(AP['v2'][k_]); d4, o4 = lnG(AP['v4'][k_]); mm = (oc & o3 & o2 & o4).astype(np.float32)
        s3 = np.abs(cv2.GaussianBlur((d3 - c) * mm, (0, 0), 3)); s2 = np.abs(cv2.GaussianBlur((d2 - c) * mm, (0, 0), 3)); s43 = np.abs(cv2.GaussianBlur((d4 - d3) * mm, (0, 0), 3)); del c, d3, d2, d4
        ero = cv2.erode(mm, np.ones((201, 201), np.uint8)) > 0
        forat = ero & (s3 < 2e-6) & (s2 > 3e-4) & (RS > 1.6); canvi = ero & (s43 > 1e-4) & (RS > 1.6); del s3, s2, s43
        n, lab, st, _ = cv2.connectedComponentsWithStats(forat.astype(np.uint8), 8); r1 = mesura(lab, st, n, ero)
        n2, lab2, st2, _ = cv2.connectedComponentsWithStats(canvi.astype(np.uint8), 8); r2 = mesura(lab2, st2, n2, ero)
        R[f'forats_verificador_{tren}'] = dict(resum=resum(r1), llista=r1); R[f'petjades_canviades_v4_{tren}'] = dict(resum=resum(r2), llista=r2)
        print('forats del verificador', tren, json.dumps(resum(r1)), '· petjades canviades v4', json.dumps(resum(r2)), flush=True)
        for r in r1: print('   ', r['centre'], 'σ4–40 contrast v3', r['b440']['v3']['contrast_dins_sobre_anell'], 'v4', r['b440']['v4']['contrast_dins_sobre_anell'], flush=True)
        desa()
print('FET')
