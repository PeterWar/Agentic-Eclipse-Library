"""m6_cura_petjades_v4 (V108, flat2d_v4) · DINS DE LES PETJADES, EL QUE HI POSA LA v4 ÉS CURA O INJECCIÓ? La prova s del m1 (w3), però a cada petjada.
Al compost (màscares de la V107), banda del ln σa − σb (4–40 i 1–4 px). Dins de cada petjada (la zona erosionada 21 px):
  s = (E_després − E_abans)/|Δ|²  amb  Δ = després − abans:  −1 = cura (Δ = −defecte), +1 = injecció (Δ sense relació amb el que hi ha).
  Increment v4 − v3 (el que la v4 hi afegeix), i també v3 − control i v4 − control.
NUL a la mateixa imatge: el mateix Δ posat a 12 desplaçaments de 450–900 px (on no hi ha cap petjada canviada): s_nul ≈ +1 ± la dispersió.
Petjades: les del m2 (a cada apilat, |Δ_v4 − Δ_v3| σ3 > 1·10⁻⁴; ≥ 3000 px) i els forats del verificador 3 (la v3 no hi tocava i la v2 sí).
Agregat: Σ numeradors / Σ |Δ|² per a totes les petjades d'un grup (i el mateix per a cada desplaçament nul).
Sortida: 4-RESULTATS/v108_20260926/flat2d_v4/M6_CURA_PETJADES.json   (només lectura; ~10 GB)"""
import json
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/flat2d_v4'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603
CR = A / '4-RESULTATS/v97_refundacio_20260924'; F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'
AP = {'control': dict(V=CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', A=CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', B=CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy'),
      'v2': dict(V=F2 / 'apilats/vixen_total.npy', A=F2 / 'apilats/sony_A_total.npy', B=F2 / 'apilats/cau/sony_B_total_v42.npy'),
      'v3': dict(V=F3 / 'apilats/vixen_total.npy', A=F3 / 'apilats/sony_A_total.npy', B=F3 / 'apilats/cau/sony_B_total_v42.npy'),
      'v4': dict(V=OUT / 'apilats/vixen_total.npy', A=OUT / 'apilats/sony_A_total.npy', B=OUT / 'apilats/cau/sony_B_total_v42.npy')}
CMP = {'control': F2 / 'compost_control.npy', 'v3': F3 / 'compost_flat2d_v3.npy', 'v4': OUT / 'compost_flat2d_v4.npy'}
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; del yy, xx
def lnG(p):
    x = np.asarray(np.load(p, mmap_mode='r')[..., 1], np.float32); ok = np.isfinite(x) & (x > 0)
    return np.where(ok, np.log(np.maximum(x, 1e-20)), 0).astype(np.float32), ok
# 1 · les petjades (el mateix criteri que m2)
REG = {}; tot_canvi = np.zeros((H, W), bool)
for tren, k_ in (('sony_A', 'A'), ('sony_B', 'B'), ('vixen', 'V')):
    c, oc = lnG(AP['control'][k_]); d3, o3 = lnG(AP['v3'][k_]); d2, o2 = lnG(AP['v2'][k_]); d4, o4 = lnG(AP['v4'][k_]); mm = (oc & o3 & o2 & o4).astype(np.float32)
    s3 = np.abs(cv2.GaussianBlur((d3 - c) * mm, (0, 0), 3)); s2 = np.abs(cv2.GaussianBlur((d2 - c) * mm, (0, 0), 3)); s43 = np.abs(cv2.GaussianBlur((d4 - d3) * mm, (0, 0), 3)); del c, d3, d2, d4
    ero = cv2.erode(mm, np.ones((201, 201), np.uint8)) > 0
    for nom, zona in (('forats_verificador', ero & (s3 < 2e-6) & (s2 > 3e-4) & (RS > 1.6)), ('petjades_canviades_v4', ero & (s43 > 1e-4) & (RS > 1.6))):
        n, lab, st, _ = cv2.connectedComponentsWithStats(zona.astype(np.uint8), 8); regs = []
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < 3000: continue
            x0, y0, w, h = st[i, :4]; f = lab[y0:y0 + h, x0:x0 + w] == i; fin = cv2.erode(f.astype(np.uint8), np.ones((21, 21), np.uint8)) > 0
            if fin.sum() < 500: continue
            regs.append((int(x0), int(y0), fin, [int(x0 + w / 2), int(y0 + h / 2)]))
        REG[f'{nom}_{tren}'] = regs
        if nom == 'petjades_canviades_v4': tot_canvi |= cv2.dilate(zona.astype(np.uint8), np.ones((101, 101), np.uint8)) > 0
    del s3, s2, s43, mm, ero
print({k: len(v) for k, v in REG.items()}, flush=True)
# 2 · el compost en banda
rng = np.random.default_rng(606); DESPL = []
while len(DESPL) < 12:
    r_ = rng.uniform(450, 900); t_ = rng.uniform(0, 2 * np.pi); DESPL.append((int(r_ * np.cos(t_)), int(r_ * np.sin(t_))))
RES = {}
for (a, b) in ((4, 40), (1, 4)):
    X = {}; M = None
    for v, p in CMP.items():
        x = np.asarray(np.load(p, mmap_mode='r'), np.float32); m = (np.isfinite(x) & (x > 0)).astype(np.float32); X[v] = np.where(m > 0, np.log(np.maximum(x, 1e-12)), 0).astype(np.float32)
        M = m if M is None else M * m; del x
    g = lambda l, s: cv2.GaussianBlur(l * M, (0, 0), s) / np.maximum(cv2.GaussianBlur(M, (0, 0), s), 1e-6)
    Bd = {v: (g(X[v], a) - g(X[v], b)).astype(np.float32) for v in X}; del X
    okM = (cv2.erode(M, np.ones((81, 81), np.uint8)) > 0) & ~tot_canvi
    for parell in (('v3', 'v4'), ('control', 'v3'), ('control', 'v4')):
        p0, p1 = parell
        for nomr, regs in REG.items():
            if not regs: continue
            num = den = 0.0; numn = np.zeros(len(DESPL)); denn = np.zeros(len(DESPL)); llista = []
            for x0, y0, fin, cen in regs:
                h, w = fin.shape; X0 = Bd[p0][y0:y0 + h, x0:x0 + w][fin].astype(np.float64); X1 = Bd[p1][y0:y0 + h, x0:x0 + w][fin].astype(np.float64); D = X1 - X0
                e0, e1, ed = (X0 ** 2).sum(), (X1 ** 2).sum(), (D ** 2).sum(); sn = []
                for j, (dx, dy) in enumerate(DESPL):
                    ya, xa = y0 + dy, x0 + dx
                    if ya < 0 or xa < 0 or ya + h > H or xa + w > W or not okM[ya:ya + h, xa:xa + w][fin].all(): sn.append(np.nan); continue
                    Xs = Bd[p0][ya:ya + h, xa:xa + w][fin].astype(np.float64); en = ((Xs + D) ** 2).sum() - (Xs ** 2).sum(); sn.append(en / ed); numn[j] += en; denn[j] += ed
                num += e1 - e0; den += ed; sn = np.array(sn, float)
                llista.append(dict(centre=cen, R_sol=round(float(RS[cen[1], cen[0]]), 2), s=round(float((e1 - e0) / ed), 3), s_nul_mitjana=round(float(np.nanmean(sn)), 3) if np.isfinite(sn).any() else None,
                                   s_nul_sd=round(float(np.nanstd(sn)), 3) if np.isfinite(sn).sum() > 2 else None, rms_delta_ppm=round(1e4 * float(np.sqrt(ed / fin.sum())), 3),
                                   energia_despres_sobre_abans=round(float(e1 / e0), 4)))
            okn = denn > 0; sn_ag = numn[okn] / denn[okn]
            RES.setdefault(f'banda_{a}_{b}', {}).setdefault(f'{p1}_menys_{p0}', {})[nomr] = dict(
                n=len(regs), s_agregat=round(float(num / den), 3), s_nul_agregat_mitjana=round(float(sn_ag.mean()), 3) if okn.any() else None,
                s_nul_agregat_sd=round(float(sn_ag.std()), 3) if okn.sum() > 2 else None, n_cura_s_menys_0=int(sum(1 for e in llista if e['s'] < 0)),
                n_injeccio_s_mes_0_5=int(sum(1 for e in llista if e['s'] > 0.5)), energia_despres_sobre_abans_agregada=round(float((num + 0) / 1), 6), petjades=llista)
            r = RES[f'banda_{a}_{b}'][f'{p1}_menys_{p0}'][nomr]; r.pop('energia_despres_sobre_abans_agregada')
            print(f'σ{a}–{b}', f'{p1} − {p0}', nomr, 'n', r['n'], 's', r['s_agregat'], 'nul', r['s_nul_agregat_mitjana'], '±', r['s_nul_agregat_sd'], 'cura', r['n_cura_s_menys_0'], 'injecció', r['n_injeccio_s_mes_0_5'], flush=True)
    del Bd, M
(OUT / 'M6_CURA_PETJADES.json').write_text(json.dumps(RES, ensure_ascii=False, indent=1) + '\n'); print('FET')
