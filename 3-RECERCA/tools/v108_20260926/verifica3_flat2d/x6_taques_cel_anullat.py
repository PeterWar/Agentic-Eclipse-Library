"""x6 (verificador adversari 3) · TAQUES DE POLS amb el cel anul·lat i selecció de punts INDEPENDENT del canvi (els punts surten de la dada, no de Δ).
Sony: Z_v = ln A_v − ln B_v (G) per a v = control, v2, v3. Vixen: Z_v = ln V_v − S (S = mitjana ln A, ln B de la Sony del control, fixa).
Banda de pols: DoG σ10 − σ60. σ robusta (MAD) de Z_control per anells d'1 R☉. Màxims locals |z| (finestra 121 px), a R > 1,6 R☉, vora ≥ 150 px.
  · N taques z ≥ 4 a cada versió; NOVES = taques de v2/v3 sense cap taca del control a ≤ 40 px amb el mateix signe i |z| ≥ 2.
  · Als màxims del control (|z| ≥ 4): residu mitjà Z_v/Z_control (0 = curada, 1 = intacta, < 0 = passada).
FORATS: a l'apilat (Sony A i Vixen), zones on la v3 no toca res (|Δ_v3| σ3 < 2·10⁻⁶) i la v2 sí (|Δ_v2| σ3 > 3·10⁻⁴): hi queda sense corregir tota la C
(també la textura comuna validada). Al compost: energia σ1–4 i σ4–40, v3/control, dins dels forats contra un anell de 60–200 px al voltant.
Sortida: 4-RESULTATS/v108_20260926/verifica3_flat2d/X6_TAQUES.json"""
import json
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica3_flat2d'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603
CR = A / '4-RESULTATS/v97_refundacio_20260924'; F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'
AP = {'control': dict(V=CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', A=CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', B=CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy'),
      'v2': dict(V=F2 / 'apilats/vixen_total.npy', A=F2 / 'apilats/sony_A_total.npy', B=F2 / 'apilats/cau/sony_B_total_v42.npy'),
      'v3': dict(V=F3 / 'apilats/vixen_total.npy', A=F3 / 'apilats/sony_A_total.npy', B=F3 / 'apilats/cau/sony_B_total_v42.npy')}
CMP = {'control': F2 / 'compost_control.npy', 'v3': F3 / 'compost_flat2d_v3.npy'}
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; del yy, xx
def lnG(p):
    x = np.asarray(np.load(p, mmap_mode='r')[..., 1], np.float32); ok = np.isfinite(x) & (x > 0)
    return np.where(ok, np.log(np.maximum(x, 1e-20)), 0).astype(np.float32), ok
R = {}
for tren in ('sony', 'vixen'):
    Z = {}; ok = None
    if tren == 'vixen':
        a, oa = lnG(AP['control']['A']); b, ob = lnG(AP['control']['B']); S = np.where(oa & ob, 0.5 * (a + b), np.where(oa, a, b)).astype(np.float32); oS = oa | ob; del a, b
    for v in AP:
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
    pics = {}
    for v in zz:
        az = np.abs(zz[v]); mx = cv2.dilate(az, np.ones((121, 121), np.uint8)); pk = okb & (az == mx) & (az >= 4)
        ys, xs = np.nonzero(pk); pics[v] = list(zip(xs.tolist(), ys.tolist(), zz[v][ys, xs].tolist()))
    zc = zz['control']
    def te_control(x, y, s):
        y0, y1, x0, x1 = max(0, y - 40), y + 41, max(0, x - 40), x + 41; w = zc[y0:y1, x0:x1]
        return bool(((np.sign(w) == np.sign(s)) & (np.abs(w) >= 2)).any())
    o = {}
    for v in zz:
        noves = [dict(x=x, y=y, z=round(s, 2), z_control=round(float(zc[y, x]), 2), R_sol=round(float(RS[y, x]), 2)) for x, y, s in pics[v] if not te_control(x, y, s)] if v != 'control' else []
        o[v] = dict(n_z4=len(pics[v]), n_noves=len(noves), noves=sorted(noves, key=lambda t: -abs(t['z']))[:12])
    cp = pics['control']
    for v in ('v2', 'v3'):
        num = sum(D[v][y, x] * D['control'][y, x] for x, y, _ in cp); den = sum(D['control'][y, x] ** 2 for x, y, _ in cp)
        fr = [float(D[v][y, x] / D['control'][y, x]) for x, y, _ in cp]
        o[v]['residu_pics_control_ponderat'] = round(float(num / den), 3) if den > 0 else None
        o[v]['residu_pics_control_mediana'] = round(float(np.median(fr)), 3) if fr else None
        o[v]['n_pics_control_intactes_residu>0.8'] = int(sum(f > 0.8 for f in fr))
    o['energia_banda_pols_sobre_control'] = {v: round(float((D[v][okb].astype(np.float64) ** 2).sum() / (D['control'][okb].astype(np.float64) ** 2).sum()), 4) for v in ('v2', 'v3')}
    R[tren] = o; print(tren, json.dumps(o), flush=True); del D, zz, sig
    (OUT / 'X6_TAQUES.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
# ---- forats: la v3 no toca res i la v2 sí
cm = {}
for v, p in CMP.items():
    x = np.asarray(np.load(p, mmap_mode='r'), np.float32); mm = (np.isfinite(x) & (x > 0)).astype(np.float32); l = np.where(mm > 0, np.log(np.maximum(x, 1e-12)), 0).astype(np.float32); del x
    g = lambda s: cv2.GaussianBlur(l * mm, (0, 0), s) / np.maximum(cv2.GaussianBlur(mm, (0, 0), s), 1e-6)
    g1 = g(1); g4 = g(4); cm[v] = dict(b14=((g1 - g4) ** 2).astype(np.float32), b440=((g4 - g(40)) ** 2).astype(np.float32)); del l, g1, g4
for tren, k_ in (('sony_A', 'A'), ('vixen', 'V')):
    c, oc = lnG(AP['control'][k_]); d3, o3 = lnG(AP['v3'][k_]); d2, o2 = lnG(AP['v2'][k_]); mm = (oc & o3 & o2).astype(np.float32)
    s3 = np.abs(cv2.GaussianBlur((d3 - c) * mm, (0, 0), 3)); s2 = np.abs(cv2.GaussianBlur((d2 - c) * mm, (0, 0), 3)); del c, d3, d2
    ero = cv2.erode(mm, np.ones((201, 201), np.uint8)) > 0
    forat = ero & (s3 < 2e-6) & (s2 > 3e-4) & (RS > 1.6); del s3, s2
    n, lab, st, _ = cv2.connectedComponentsWithStats(forat.astype(np.uint8), 8)
    grans = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 3000]
    res = []
    for i in grans:
        x0, y0, w, h = st[i, :4]; pad = 220; ya, yb, xa, xb = max(0, y0 - pad), min(H, y0 + h + pad), max(0, x0 - pad), min(W, x0 + w + pad)
        f = lab[ya:yb, xa:xb] == i; dist = cv2.distanceTransform((~f).astype(np.uint8), cv2.DIST_L2, 5); ring = (dist >= 60) & (dist < 200) & (lab[ya:yb, xa:xb] == 0) & ero[ya:yb, xa:xb]
        fin = cv2.erode(f.astype(np.uint8), np.ones((21, 21), np.uint8)) > 0
        if fin.sum() < 500 or ring.sum() < 2000: continue
        e = {}
        for b in ('b14', 'b440'):
            rin = cm['v3'][b][ya:yb, xa:xb][fin].mean() / cm['control'][b][ya:yb, xa:xb][fin].mean(); rout = cm['v3'][b][ya:yb, xa:xb][ring].mean() / cm['control'][b][ya:yb, xa:xb][ring].mean()
            e[b] = dict(dins=round(float(rin), 3), anell=round(float(rout), 3), contrast_dins_sobre_anell=round(float(rin / rout), 3))
        res.append(dict(centre=[int(x0 + w / 2), int(y0 + h / 2)], area_px=int(st[i, cv2.CC_STAT_AREA]), R_sol=round(float(RS[int(y0 + h / 2), int(x0 + w / 2)]), 2), **e))
    R[f'forats_{tren}'] = dict(n=len(res), llista=res); print('forats', tren, json.dumps(res), flush=True)
    (OUT / 'X6_TAQUES.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
