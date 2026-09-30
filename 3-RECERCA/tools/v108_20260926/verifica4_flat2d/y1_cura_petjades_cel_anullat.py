"""y1 (verificador adversari 4) · EL QUE LA v4 AFEGEIX A LES PETJADES, ÉS CURA O INJECCIÓ? Prova s AMB EL CEL ANUL·LAT (no al compost).
Sony: Z_v = ln A_v − ln B_v (canal G). Vixen: Z_v = ln V_v − S, S = mitjana de ln A i ln B de la Sony del CONTROL (fixa: Δ_Z = Δ_V).
Petjades: definides pel CANVI de l'apilat, sense mirar cap fitxer de l'autor: |G3(ln X_v4 − ln X_v3)| > 5·10⁻⁵ (X = A, B o V), components ≥ 300 px,
dilatades 15 px. S'hi fa servir la zona SENCERA (vores incloses, a diferència del m6, que erosiona 21 px): si hi hagués una costura, sortiria.
Per a cada banda del Z (DoG σa − σb: 1–4, 4–40, 2–60, 10–60) i cada petjada:  s = (|X + D|² − |X|²)/|D|², X = banda de Z_control, D = banda del canvi.
  Si D = −k·(defecte): s = 1 − 2/k. −1 = cura exacta (k = 1); < −1 = cura curta (k < 1, en queda); entre −1 i +1 = passa de llarg (k > 1; s = 0 és
  k = 2); +1 = el canvi no té res a veure amb la dada (injecció).
Canvis: v4 − v3 (el que afegeix la v4), v4 − control, v3 − control.
NUL a la mateixa imatge: el mateix D posat a 24 desplaçaments de 450–1200 px (llavor 4242, diferent de la de l'autor), on no hi ha cap petjada
(de cap dels apilats) ni vora: s_nul ≈ +1 ± dispersió. Agregat de grup = Σ num / Σ |D|² (i el mateix per a cada desplaçament).
Grups: per tren; per anell (R < 6, 6–11, > 11 R☉); a la Vixen, les petjades de les estructures amb â = 0; a la Sony, les de R > 11 (vora).
Cada petjada s'associa a l'estructura de G1_PORTA_V4 més propera (≤ 80 px) només per etiquetar-la (â, regla).
També COSTURA: rms de la banda σ1–4 del canvi v4 − v3 a l'anell de la vora de la petjada (±6 px de la frontera de la zona sense dilatar) contra
l'interior i contra el soroll (la mateixa banda de Z_control al mateix anell).
Sortida: 4-RESULTATS/v108_20260926/verifica4_flat2d/Y1_CURA_PETJADES.json (només lectura; ~12 GB)."""
import json, sys, time
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica4_flat2d'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
CR = A / '4-RESULTATS/v97_refundacio_20260924'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'; F4 = A / '4-RESULTATS/v108_20260926/flat2d_v4'
AP = {'control': dict(V=CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', A=CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', B=CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy'),
      'v3': dict(V=F3 / 'apilats/vixen_total.npy', A=F3 / 'apilats/sony_A_total.npy', B=F3 / 'apilats/cau/sony_B_total_v42.npy'),
      'v4': dict(V=F4 / 'apilats/vixen_total.npy', A=F4 / 'apilats/sony_A_total.npy', B=F4 / 'apilats/cau/sony_B_total_v42.npy')}
t0 = time.time()
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL; del yy, xx
def lnG(p):
    x = np.asarray(np.load(p, mmap_mode='r')[..., 1], np.float32); ok = np.isfinite(x) & (x > 0)
    return np.where(ok, np.log(np.maximum(x, 1e-20)), 0).astype(np.float32), ok
EST = {}
for tren, fn in (('sony_A', 'SONYTOT'), ('sony_B', 'SONYTOT'), ('vixen', 'VIXEN')):
    g1 = json.loads((F4 / f'flat2d/G1_PORTA_V4_{fn}.json').read_text())['grups'][tren]['decisions']
    h1 = json.loads((F4 / f'flat2d/H1_ENCONGIDA_{fn}.json').read_text())['grups'][tren]['estructures']
    EST[tren] = [(np.array(d['centre_llenc'], float), k, h1.get(k, {}).get('a_encongida'), h1.get(k, {}).get('regla'), d.get('aplica')) for k, d in g1.items() if d.get('centre_llenc')]
def etiqueta(tren, c):
    if not EST[tren]: return None
    ds = [np.hypot(*(e[0] - c)) for e in EST[tren]]; i = int(np.argmin(ds))
    if ds[i] > 80: return None
    e = EST[tren][i]; return dict(id=e[1], a_encongida=e[2], regla=e[3], aplicada_v3=e[4], dist=round(float(ds[i]), 1))
# 1 · petjades, per apilat, a partir del canvi v4 − v3
PET = {}; TOT = np.zeros((H, W), bool); OK = {}
for tren, k_ in (('sony_A', 'A'), ('sony_B', 'B'), ('vixen', 'V')):
    d3, o3 = lnG(AP['v3'][k_]); d4, o4 = lnG(AP['v4'][k_]); m = (o3 & o4).astype(np.float32)
    s43 = np.abs(cv2.GaussianBlur((d4 - d3) * m, (0, 0), 3)); del d3, d4
    z = ((s43 > 5e-5) & (m > 0)).astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(z, 8); regs = []
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < 300: continue
        x0, y0, w, h = st[i, :4]; pad = 24; xa, ya, xb, yb = max(0, x0 - pad), max(0, y0 - pad), min(W, x0 + w + pad), min(H, y0 + h + pad)
        f0 = (lab[ya:yb, xa:xb] == i).astype(np.uint8); f = cv2.dilate(f0, np.ones((31, 31), np.uint8)) > 0
        vora = (cv2.dilate(f0, np.ones((13, 13), np.uint8)) > 0) & ~(cv2.erode(f0, np.ones((13, 13), np.uint8)) > 0)
        inter = cv2.erode(f0, np.ones((13, 13), np.uint8)) > 0
        cen = np.array([x0 + w / 2, y0 + h / 2]); regs.append(dict(xa=int(xa), ya=int(ya), f=f, vora=vora, inter=inter, centre=[int(cen[0]), int(cen[1])],
                                                                R_sol=round(float(RS[int(cen[1]), int(cen[0])]), 2), area=int(st[i, cv2.CC_STAT_AREA]), max_canvi_ppm=round(1e4 * float(s43[y0:y0 + h, x0:x0 + w].max()), 3), est=etiqueta(tren, cen)))
        TOT[ya:yb, xa:xb] |= f
    PET[tren] = regs; OK[tren] = m > 0; print(tren, 'petjades', len(regs), f'{time.time()-t0:.0f}s', flush=True); del s43, lab, z
TOTD = cv2.dilate(TOT.astype(np.uint8), np.ones((61, 61), np.uint8)) > 0
rng = np.random.default_rng(4242); DESPL = []
while len(DESPL) < 24:
    r_ = rng.uniform(450, 1200); t_ = rng.uniform(0, 2 * np.pi); DESPL.append((int(r_ * np.cos(t_)), int(r_ * np.sin(t_))))
BANDES = [(1, 4), (4, 40), (2, 60), (10, 60)]
R = dict(n_petjades={k: len(v) for k, v in PET.items()}, desplacaments=DESPL)
for tz in ('sony', 'vixen'):
    Z = {}; okz = None
    if tz == 'vixen':
        a, oa = lnG(AP['control']['A']); b, ob = lnG(AP['control']['B']); S = np.where(oa & ob, 0.5 * (a + b), np.where(oa, a, b)).astype(np.float32); oS = oa | ob; del a, b, oa, ob
    for v in AP:
        if tz == 'sony':
            a, oa = lnG(AP[v]['A']); b, ob = lnG(AP[v]['B']); o = oa & ob; z = a - b; del a, b
        else:
            a, oa = lnG(AP[v]['V']); o = oa & oS; z = a - S; del a
        Z[v] = np.where(o, z, 0).astype(np.float32); okz = o if okz is None else okz & o; del z
    if tz == 'vixen': del S
    m = (okz & (DL > 40)).astype(np.float32); okb = cv2.erode(m, np.ones((121, 121), np.uint8)) > 0
    trens = ['sony_A', 'sony_B'] if tz == 'sony' else ['vixen']
    for (sa, sb) in BANDES:
        ng = lambda x, s: cv2.GaussianBlur(x * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
        Bc = (ng(Z['control'], sa) - ng(Z['control'], sb)).astype(np.float32); B3 = (ng(Z['v3'], sa) - ng(Z['v3'], sb)).astype(np.float32); B4 = (ng(Z['v4'], sa) - ng(Z['v4'], sb)).astype(np.float32)
        CANVIS = {'v4_menys_v3': (B3, B4 - B3), 'v4_menys_control': (Bc, B4 - Bc), 'v3_menys_control': (Bc, B3 - Bc)}
        okn = okb & ~TOTD
        for tren in trens:
            for nomc, (X0full, Dfull) in CANVIS.items():
                grups = {}; llista = []
                for p in PET[tren]:
                    f = p['f']; h, w = f.shape; ya, xa = p['ya'], p['xa']; fv = f & okb[ya:ya + h, xa:xa + w]
                    if fv.sum() < 200: continue
                    X = X0full[ya:ya + h, xa:xa + w][fv].astype(np.float64); D = Dfull[ya:ya + h, xa:xa + w][fv].astype(np.float64)
                    ed = (D ** 2).sum()
                    if ed <= 0: continue
                    num = ((X + D) ** 2).sum() - (X ** 2).sum(); nn = np.full(len(DESPL), np.nan); dd = np.full(len(DESPL), np.nan)
                    for j, (dx, dy) in enumerate(DESPL):
                        yb_, xb_ = ya + dy, xa + dx
                        if yb_ < 0 or xb_ < 0 or yb_ + h > H or xb_ + w > W or not okn[yb_:yb_ + h, xb_:xb_ + w][fv].all(): continue
                        Xs = X0full[yb_:yb_ + h, xb_:xb_ + w][fv].astype(np.float64); nn[j] = ((Xs + D) ** 2).sum() - (Xs ** 2).sum(); dd[j] = ed
                    e = p['est'] or {}
                    claus = ['tots', 'R<6' if p['R_sol'] < 6 else ('R6-11' if p['R_sol'] < 11 else 'R>11')]
                    if tren == 'vixen' and e.get('a_encongida') == 0: claus.append('vixen_a_zero')
                    if e.get('regla') == 'encongida': claus.append('encongides')
                    if e.get('aplicada_v3'): claus.append('aplicades_v3')
                    if not e: claus.append('sense_estructura_propera')
                    for c in claus:
                        g = grups.setdefault(c, dict(num=0.0, den=0.0, nn=np.zeros(len(DESPL)), dd=np.zeros(len(DESPL)), n=0, ncura=0, ninj=0))
                        g['num'] += num; g['den'] += ed; ok_ = np.isfinite(nn); g['nn'][ok_] += nn[ok_]; g['dd'][ok_] += dd[ok_]; g['n'] += 1
                        g['ncura'] += int(num / ed < 0); g['ninj'] += int(num / ed > 0.5)
                    if (sa, sb) in ((4, 40), (2, 60)) and nomc == 'v4_menys_v3':
                        okj = np.isfinite(nn)
                        llista.append(dict(centre=p['centre'], R_sol=p['R_sol'], area=p['area'], est=e or None, s=round(float(num / ed), 3),
                                           s_nul=round(float(np.mean(nn[okj] / dd[okj])), 3) if okj.sum() > 3 else None, s_nul_sd=round(float(np.std(nn[okj] / dd[okj])), 3) if okj.sum() > 3 else None,
                                           rms_canvi_ppm=round(1e4 * float(np.sqrt(ed / fv.sum())), 3), rms_dada_ppm=round(1e4 * float(np.sqrt((X ** 2).mean())), 3)))
                out = {}
                for c, g in grups.items():
                    okj = g['dd'] > 0; sn = g['nn'][okj] / g['dd'][okj]
                    out[c] = dict(n=g['n'], s=round(g['num'] / g['den'], 3), s_nul=round(float(sn.mean()), 3) if okj.sum() > 3 else None,
                                  s_nul_sd=round(float(sn.std()), 3) if okj.sum() > 3 else None, z=round(float((g['num'] / g['den'] - sn.mean()) / sn.std()), 2) if okj.sum() > 3 and sn.std() > 0 else None,
                                  n_s_menys_0=g['ncura'], n_s_mes_0_5=g['ninj'])
                R.setdefault(tren, {}).setdefault(f'banda_{sa}_{sb}', {})[nomc] = out
                if llista: R[tren].setdefault('petjades', {})[f'banda_{sa}_{sb}'] = llista
                print(tren, f'σ{sa}–{sb}', nomc, json.dumps(out.get('tots')), f'{time.time()-t0:.0f}s', flush=True)
        # costura: només a σ1–4
        if (sa, sb) == (1, 4):
            for tren in trens:
                ev = ei = en = 0.0; nv = ni = 0; per = []
                for p in PET[tren]:
                    h, w = p['f'].shape; ya, xa = p['ya'], p['xa']; okp = okb[ya:ya + h, xa:xa + w]
                    v_ = p['vora'] & okp; i_ = p['inter'] & okp
                    if v_.sum() < 50 or i_.sum() < 50: continue
                    Dp = B4[ya:ya + h, xa:xa + w].astype(np.float64) - B3[ya:ya + h, xa:xa + w]; Xp = Bc[ya:ya + h, xa:xa + w].astype(np.float64)
                    ev += (Dp[v_] ** 2).sum(); nv += v_.sum(); ei += (Dp[i_] ** 2).sum(); ni += i_.sum(); en += (Xp[v_] ** 2).sum()
                    per.append((float(np.sqrt((Dp[v_] ** 2).mean()) / max(np.sqrt((Dp[i_] ** 2).mean()), 1e-12)), p['centre']))
                per.sort(key=lambda t: -t[0])
                R.setdefault(tren, {})['costura_sigma1_4'] = dict(rms_canvi_vora_ppm=round(1e4 * float(np.sqrt(ev / max(nv, 1))), 4), rms_canvi_interior_ppm=round(1e4 * float(np.sqrt(ei / max(ni, 1))), 4),
                                                                   rms_soroll_dada_vora_ppm=round(1e4 * float(np.sqrt(en / max(nv, 1))), 3), pitjors_vora_sobre_interior=[dict(q=round(q, 2), centre=c) for q, c in per[:6]])
                print(tren, 'costura', json.dumps(R[tren]['costura_sigma1_4']), flush=True)
        del Bc, B3, B4, CANVIS
        (OUT / 'Y1_CURA_PETJADES.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
    del Z
(OUT / 'Y1_CURA_PETJADES.json').write_text(json.dumps(R, ensure_ascii=False, indent=1)); print('FET', f'{time.time()-t0:.0f}s')
