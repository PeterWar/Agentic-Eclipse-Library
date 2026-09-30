"""m7_pols_moguda_v5 (V108, flat2d_v5) · LA POLS MOGUDA: EL QUE HI FA LA v5, ÉS CURA? Prova s AMB EL CEL ANUL·LAT i nuls a la mateixa imatge
(el mètode del y1 del verificador 4, amb una llavor pròpia), als apilats (no al compost).
Vixen: Z_v = ln V_v − S, S = la mitjana de ln A i ln B de la Sony del CONTROL (fixa: ΔZ = ΔV). Sony: Z_v = ln A_v − ln B_v (canal G).
Petjades: les del verificador, definides pel CANVI v4 − v3 de cada apilat (|G3| > 5·10⁻⁵, components ≥ 300 px, dilatades 15 px); cada petjada
s'etiqueta amb l'estructura de G1_PORTA_V4 més propera (≤ 80 px). Grups de la Vixen: «pols_moguda_5» (les 5 de l'encàrrec: 73, 2, 32, 66, 57),
«a_zero_4» (les 4 amb â = 0, el grup del verificador), cadascuna sola, i «resta» (la resta de petjades de la Vixen).
Per a cada banda del Z (DoG σa − σb, px del llenç) i cada canvi D:  s = (|X + D|² − |X|²)/|D|², X = la banda del Z de la versió de partida.
  −1 = cura exacta; < −1 = cura curta; entre −1 i +1 = passa de llarg (0 = el doble); +1 = com el nul (injecció).
  Agregat de grup = Σ num / Σ |D|²; NUL = el mateix D a 24 desplaçaments de 450–1200 px (llavor 5055), sense petjades ni vora.
Canvis: v5 − v4 (el que treu la v5), v5 − v3, v5 − control, v4 − v3, v4 − control, v3 − control.
També, a la banda de cada canvi: r_v = ⟨X_v, D43⟩/|D43|² (quant de «la direcció del canvi de la v4» porta encara la dada de cada versió:
0 = res; −0,5 = la meitat del canvi de la v4, en el sentit que el cura; +0,5 = el canvi de la v4 hi va de més la meitat).
SONY (per a la declaració del §3, sense canviar res: els apilats de la Sony de la v5 són els de la v4 bit a bit): la mateixa prova per al canvi
v4 − v3 a les petjades de cada apuntament, per bandes fines (1–2, 2–4, 4–10, 10–20, 20–40, 40–80 px), per saber a quina escala queda curta.
Sortida: 4-RESULTATS/v108_20260926/flat2d_v5/M7_POLS_MOGUDA.json (només lectura; ~12 GB)."""
import json, time
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/flat2d_v5'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
CR = A / '4-RESULTATS/v97_refundacio_20260924'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'; F4 = A / '4-RESULTATS/v108_20260926/flat2d_v4'; F5 = OUT
AP = {'control': dict(V=CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', A=CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', B=CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy'),
      'v3': dict(V=F3 / 'apilats/vixen_total.npy', A=F3 / 'apilats/sony_A_total.npy', B=F3 / 'apilats/cau/sony_B_total_v42.npy'),
      'v4': dict(V=F4 / 'apilats/vixen_total.npy', A=F4 / 'apilats/sony_A_total.npy', B=F4 / 'apilats/cau/sony_B_total_v42.npy'),
      'v5': dict(V=F5 / 'apilats/vixen_total.npy', A=F5 / 'apilats/sony_A_total.npy', B=F5 / 'apilats/cau/sony_B_total_v42.npy')}
POLS = [73, 2, 32, 66, 57]; A_ZERO = [73, 2, 32, 66]
t0 = time.time()
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL; del yy, xx
def lnG(p):
    x = np.asarray(np.load(p, mmap_mode='r')[..., 1], np.float32); ok = np.isfinite(x) & (x > 0)
    return np.where(ok, np.log(np.maximum(x, 1e-20)), 0).astype(np.float32), ok
EST = {}
for tren, fn in (('sony_A', 'SONYTOT'), ('sony_B', 'SONYTOT'), ('vixen', 'VIXEN')):
    g1 = json.loads((F4 / f'flat2d/G1_PORTA_V4_{fn}.json').read_text())['grups'][tren]['decisions']
    h1 = json.loads((F4 / f'flat2d/H1_ENCONGIDA_{fn}.json').read_text())['grups'][tren]['estructures']
    EST[tren] = [(np.array(d['centre_llenc'], float), int(k), h1.get(k, {}).get('a_encongida'), h1.get(k, {}).get('regla'), d.get('aplica')) for k, d in g1.items() if d.get('centre_llenc')]
def etiqueta(tren, c):
    ds = [np.hypot(*(e[0] - c)) for e in EST[tren]]; i = int(np.argmin(ds))
    if ds[i] > 80: return {}
    e = EST[tren][i]; return dict(id=e[1], a_encongida=e[2], regla=e[3], aplicada_v3=e[4], dist=round(float(ds[i]), 1))
# 1 · petjades del verificador (canvi v4 − v3 de cada apilat)
PET = {}; TOT = np.zeros((H, W), bool)
for tren, k_ in (('sony_A', 'A'), ('sony_B', 'B'), ('vixen', 'V')):
    d3, o3 = lnG(AP['v3'][k_]); d4, o4 = lnG(AP['v4'][k_]); m = (o3 & o4).astype(np.float32)
    s43 = np.abs(cv2.GaussianBlur((d4 - d3) * m, (0, 0), 3)); del d3, d4
    z = ((s43 > 5e-5) & (m > 0)).astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(z, 8); regs = []
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < 300: continue
        x0, y0, w, h = st[i, :4]; pad = 24; xa, ya, xb, yb = max(0, x0 - pad), max(0, y0 - pad), min(W, x0 + w + pad), min(H, y0 + h + pad)
        f0 = (lab[ya:yb, xa:xb] == i).astype(np.uint8); f = cv2.dilate(f0, np.ones((31, 31), np.uint8)) > 0
        cen = np.array([x0 + w / 2, y0 + h / 2]); regs.append(dict(xa=int(xa), ya=int(ya), f=f, centre=[int(cen[0]), int(cen[1])], R_sol=round(float(RS[int(cen[1]), int(cen[0])]), 2),
                                                                area=int(st[i, cv2.CC_STAT_AREA]), est=etiqueta(tren, cen)))
        TOT[ya:yb, xa:xb] |= f
    PET[tren] = regs; print(tren, 'petjades', len(regs), f'{time.time()-t0:.0f}s', flush=True); del s43, lab, z
TOTD = cv2.dilate(TOT.astype(np.uint8), np.ones((61, 61), np.uint8)) > 0
rng = np.random.default_rng(5055); DESPL = []
while len(DESPL) < 24:
    r_ = rng.uniform(450, 1200); t_ = rng.uniform(0, 2 * np.pi); DESPL.append((int(r_ * np.cos(t_)), int(r_ * np.sin(t_))))
R = dict(n_petjades={k: len(v) for k, v in PET.items()}, desplacaments=DESPL, llavor=5055,
         petjades_pols_moguda=[dict(centre=p['centre'], area=p['area'], R_sol=p['R_sol'], est=p['est']) for p in PET['vixen'] if p['est'].get('id') in POLS])
print('petjades de pols moguda:', [(p['centre'], p['est'].get('id')) for p in PET['vixen'] if p['est'].get('id') in POLS], flush=True)
def s_grup(Xf, Df, petjades, okb, okn, claus_de):
    """agregat s i nul per grups; claus_de(p) → llista de grups de la petjada"""
    grups = {}; per = []
    for p in petjades:
        f = p['f']; h, w = f.shape; ya, xa = p['ya'], p['xa']; fv = f & okb[ya:ya + h, xa:xa + w]
        if fv.sum() < 200: continue
        X = Xf[ya:ya + h, xa:xa + w][fv].astype(np.float64); D = Df[ya:ya + h, xa:xa + w][fv].astype(np.float64); ed = (D ** 2).sum()
        cl = claus_de(p)
        if ed <= 0:
            for c in cl: grups.setdefault(c, dict(num=0.0, den=0.0, nn=np.zeros(len(DESPL)), dd=np.zeros(len(DESPL)), n=0, n_D_zero=0))['n_D_zero'] += 1
            continue
        num = ((X + D) ** 2).sum() - (X ** 2).sum(); nn = np.full(len(DESPL), np.nan)
        for j, (dx, dy) in enumerate(DESPL):
            yb_, xb_ = ya + dy, xa + dx
            if yb_ < 0 or xb_ < 0 or yb_ + h > H or xb_ + w > W or not okn[yb_:yb_ + h, xb_:xb_ + w][fv].all(): continue
            Xs = Xf[yb_:yb_ + h, xb_:xb_ + w][fv].astype(np.float64); nn[j] = ((Xs + D) ** 2).sum() - (Xs ** 2).sum()
        for c in cl:
            g = grups.setdefault(c, dict(num=0.0, den=0.0, nn=np.zeros(len(DESPL)), dd=np.zeros(len(DESPL)), n=0, n_D_zero=0))
            g['num'] += num; g['den'] += ed; ok_ = np.isfinite(nn); g['nn'][ok_] += nn[ok_]; g['dd'][ok_] += ed; g['n'] += 1
        okj = np.isfinite(nn)
        per.append(dict(centre=p['centre'], id=p['est'].get('id'), s=round(float(num / ed), 3), s_nul=round(float(np.mean(nn[okj] / ed)), 3) if okj.sum() > 3 else None,
                        s_nul_sd=round(float(np.std(nn[okj] / ed)), 3) if okj.sum() > 3 else None, rms_canvi_1e4=round(1e4 * float(np.sqrt(ed / fv.sum())), 3)))
    out = {}
    for c, g in grups.items():
        if g['den'] <= 0: out[c] = dict(n=g['n'], n_D_zero=g['n_D_zero'], s=None); continue
        okj = g['dd'] > 0; sn = g['nn'][okj] / g['dd'][okj]; s = g['num'] / g['den']
        out[c] = dict(n=g['n'], n_D_zero=g['n_D_zero'], s=round(s, 3), s_nul=round(float(sn.mean()), 3) if okj.sum() > 3 else None, s_nul_sd=round(float(sn.std()), 3) if okj.sum() > 3 else None,
                      z=round(float((s - sn.mean()) / sn.std()), 2) if okj.sum() > 3 and sn.std() > 0 else None, k_canvi_sobre_defecte=round(2 / (1 - s), 3) if s < 1 else None)
    return out, per
def r_dir(Xf, Df, petjades, okb, claus_de):
    """r = ⟨X, D⟩/|D|² per grups (quant de la direcció D porta X)"""
    g = {}
    for p in petjades:
        f = p['f']; h, w = f.shape; ya, xa = p['ya'], p['xa']; fv = f & okb[ya:ya + h, xa:xa + w]
        if fv.sum() < 200: continue
        X = Xf[ya:ya + h, xa:xa + w][fv].astype(np.float64); D = Df[ya:ya + h, xa:xa + w][fv].astype(np.float64)
        for c in claus_de(p): q = g.setdefault(c, [0.0, 0.0]); q[0] += (X * D).sum(); q[1] += (D ** 2).sum()
    return {c: (round(v[0] / v[1], 3) if v[1] > 0 else None) for c, v in g.items()}
def claus_vixen(p):
    i = p['est'].get('id'); c = []
    if i in POLS: c += ['pols_moguda_5', f'pols_{i}']
    else: c.append('resta')
    if i in A_ZERO: c.append('a_zero_4')
    return c
# 2 · VIXEN
a, oa = lnG(AP['control']['A']); b, ob = lnG(AP['control']['B']); S = np.where(oa & ob, 0.5 * (a + b), np.where(oa, a, b)).astype(np.float32); oS = oa | ob; del a, b, oa, ob
Z = {}; okz = None
for v in AP:
    x, o = lnG(AP[v]['V']); o &= oS; Z[v] = np.where(o, x - S, 0).astype(np.float32); okz = o if okz is None else okz & o; del x
del S
m = (okz & (DL > 40)).astype(np.float32); okb = cv2.erode(m, np.ones((121, 121), np.uint8)) > 0; okn = okb & ~TOTD
ng = lambda x, s: cv2.GaussianBlur(x * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
CANVIS = [('v5_menys_v4', 'v4', 'v5'), ('v5_menys_v3', 'v3', 'v5'), ('v5_menys_control', 'control', 'v5'), ('v4_menys_v3', 'v3', 'v4'), ('v4_menys_control', 'control', 'v4'), ('v3_menys_control', 'control', 'v3')]
R['vixen'] = {}
for (sa, sb) in [(1, 4), (4, 40), (2, 60), (10, 60)]:
    Bd = {v: (ng(Z[v], sa) - ng(Z[v], sb)).astype(np.float32) for v in Z}; ob_ = {}
    for nomc, v0, v1 in CANVIS:
        out, per = s_grup(Bd[v0], Bd[v1] - Bd[v0], PET['vixen'], okb, okn, claus_vixen)
        ob_[nomc] = dict(grups=out, petjades_pols_moguda=[q for q in per if q['id'] in POLS])
        print('vixen', f'σ{sa}–{sb}', nomc, json.dumps({k: out.get(k) for k in ('pols_moguda_5', 'a_zero_4', 'resta')}), f'{time.time()-t0:.0f}s', flush=True)
    D43 = Bd['v4'] - Bd['v3']; ob_['r_direccio_canvi_v4'] = {v: r_dir(Bd[v], D43, PET['vixen'], okb, claus_vixen) for v in ('control', 'v3', 'v4', 'v5')}
    print('vixen', f'σ{sa}–{sb}', 'r (direcció del canvi de la v4)', json.dumps({v: {k: x.get(k) for k in ('pols_moguda_5', 'a_zero_4')} for v, x in ob_['r_direccio_canvi_v4'].items()}), flush=True)
    R['vixen'][f'banda_{sa}_{sb}'] = ob_; del Bd, D43
    (OUT / 'M7_POLS_MOGUDA.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
del Z
# 3 · SONY (declaració): el canvi v4 − v3 (= v5 − v3) per bandes fines, a les petjades de cada apuntament
Z = {}; okz = None
for v in ('v3', 'v4', 'v5'):
    a, oa = lnG(AP[v]['A']); b, ob = lnG(AP[v]['B']); o = oa & ob; Z[v] = np.where(o, a - b, 0).astype(np.float32); okz = o if okz is None else okz & o; del a, b
R['sony_v5_igual_v4'] = bool(np.array_equal(Z['v4'], Z['v5'])); del Z['v5']
m = (okz & (DL > 40)).astype(np.float32); okb = cv2.erode(m, np.ones((121, 121), np.uint8)) > 0; okn = okb & ~TOTD
def claus_sony(p):
    e = p['est']; c = ['tots']
    if e.get('regla') == 'encongida': c.append('encongides')
    if e.get('aplicada_v3'): c.append('aplicades_v3')
    c.append('R<6' if p['R_sol'] < 6 else ('R6-11' if p['R_sol'] < 11 else 'R>11'))
    return c
R['sony'] = {}
for (sa, sb) in [(1, 2), (2, 4), (4, 10), (10, 20), (20, 40), (40, 80), (4, 40)]:
    Bd = {v: (ng(Z[v], sa) - ng(Z[v], sb)).astype(np.float32) for v in Z}
    for tren in ('sony_A', 'sony_B'):
        out, _ = s_grup(Bd['v3'], Bd['v4'] - Bd['v3'], PET[tren], okb, okn, claus_sony)
        R['sony'].setdefault(tren, {})[f'banda_{sa}_{sb}'] = out
        print(tren, f'σ{sa}–{sb}', 'v4_menys_v3', json.dumps({k: out.get(k) for k in ('tots', 'encongides')}), f'{time.time()-t0:.0f}s', flush=True)
    del Bd
(OUT / 'M7_POLS_MOGUDA.json').write_text(json.dumps(R, ensure_ascii=False, indent=1)); print('FET', f'{time.time()-t0:.0f}s')
