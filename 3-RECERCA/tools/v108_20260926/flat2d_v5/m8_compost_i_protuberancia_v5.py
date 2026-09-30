"""m8_compost_i_protuberancia_v5 (V108, flat2d_v5) · EL QUE CANVIA LA v5 A LA IMATGE: (A) el compost a les 5 petjades de pols moguda,
(B) la protuberància (franja, base, filtres, compost) i (C) Brno a 1,02–1,5 R☉.
(A) COMPOST a les petjades de pols moguda (les del verificador: canvi v4 − v3 de l'apilat de la Vixen, |G3| > 5·10⁻⁵, dilatades 15 px; la de
    l'estructura 73, 2, 32, 66 o 57): per a cada parell (v4/v3, v5/v3, v5/v4, v4/control, v5/control), el màxim i el rms de |G3(ln ratio)| (σ 3 px,
    la mètrica de la Y7 del verificador) i, com a referència, el mateix a l'anell de 30–90 px de fora de la petjada.
(B) PROTUBERÀNCIA: als 7 píxels fràgils (P1_PROTUBERANCIA.json de la v5), als 3 a tocar del llindar i al veí (4897, 3786): la franja (G), la
    base_G lineal, la base de pantalla (capa 3, u16), els 16 filtres (valor i alfa de filtres_v108, i L{id}_G/alfa de l'estat) i el compost,
    per al control (la V107), la v4 i la v5. A la caixa de 81×81 px al voltant: el màxim de |ln(v/control)| de cada capa i del compost.
    I la mesura del verificador 4 (y3): dins del domini de la franja, r = ln(base_v/base_control) per fragilitat f (< 0,002, 0,002–0,01, > 0,01).
(C) BRNO (còpia del y6 del verificador 4): r, amplitud a i energia de la resta del DoG del ln (compost, base) contra el DoG del ln de Brno
    (L230–232 del control), anells 1,02–1,5 i 1,5–2,5 R☉, bandes σ1–8, 2–16, 4–40; control, v3, v4, v5.
(D) COMPOST a les petjades de pols moguda, PER BANDES: rms del DoG σ1–4 i σ4–40 de ln(v/ref) dins de la petjada i a l'anell de 30–90 px.
Ús: m8_compost_i_protuberancia_v5.py [ABCD]   (cada part s'afegeix al JSON)
v4: la base, els filtres i l'estat de la v4 són a la Paperera (~/.Trash/Eclipse_V108_flat2d_v4_intermedis_20260927/cadena/flat2d_v4:
base_100113, filtres_v108, estat_v108), només lectura. Sortida: 4-RESULTATS/v108_20260926/flat2d_v5/M8_COMPOST_PROTUBERANCIA.json (~10 GB)."""
import json, time, sys
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/flat2d_v5'; CAD = A / '4-RESULTATS/v108_20260926/cadena'
T4 = Path.home() / '.Trash/Eclipse_V108_flat2d_v4_intermedis_20260927/cadena/flat2d_v4'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'; F4 = A / '4-RESULTATS/v108_20260926/flat2d_v4'
CMP = {'control': F2 / 'compost_control.npy', 'v3': F3 / 'compost_flat2d_v3.npy', 'v4': F4 / 'compost_flat2d_v4.npy', 'v5': OUT / 'compost_flat2d_v5.npy'}
BASEG = {'control': CAD / 'control/lineal/base_G.npy', 'v3': CAD / 'flat2d_v3/lineal/base_G.npy', 'v4': CAD / 'flat2d_v4/lineal/base_G.npy', 'v5': CAD / 'flat2d_v5/lineal/base_G.npy'}
BASE16 = {'control': CAD / 'control/base/base_v108_final_u16.npy', 'v4': T4 / 'base_100113/base_v108_final_u16.npy', 'v5': CAD / 'flat2d_v5/base/base_v108_final_u16.npy'}
FILT = {'control': CAD / 'control/filtres_v108', 'v4': T4 / 'filtres_v108', 'v5': CAD / 'flat2d_v5/filtres_v108'}
ESTAT = {'control': CAD / 'control/estat_v108', 'v4': T4 / 'estat_v108', 'v5': CAD / 'flat2d_v5/estat_v108'}
FR = {'control': CAD / 'control/franja/A3C_franja_silueta.npz', 'v4': CAD / 'flat2d_v4/franja/A3C_franja_silueta.npz', 'v5': CAD / 'flat2d_v5/franja/A3C_franja_silueta.npz'}
TAG = {41: 'P01_NRGF', 42: 'P01_NRGF_extrap', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 47: '03', 48: '03v30', 49: '07',
       50: '01', 51: '04', 52: '05', 53: '06', 54: 'P03_MGN', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
POLS = [73, 2, 32, 66, 57]; t0 = time.time(); R = {}
part = sys.argv[1] if len(sys.argv) > 1 else 'ABC'
OUTJ = OUT / 'M8_COMPOST_PROTUBERANCIA.json'
if OUTJ.exists(): R = json.loads(OUTJ.read_text())
def desa(): OUTJ.write_text(json.dumps(R, ensure_ascii=False, indent=1) + '\n')
def carrega(p, sl=None):
    x = np.load(p, mmap_mode='r'); return np.asarray(x if sl is None else x[sl], np.float32)
# ------------------------------------------------------------------------------------------------------------------------------------
# (A) compost a les petjades de pols moguda
# ------------------------------------------------------------------------------------------------------------------------------------
if 'A' in part:
    G1 = json.loads((F4 / 'flat2d/G1_PORTA_V4_VIXEN.json').read_text())['grups']['vixen']['decisions']; CEN = {k: np.array(G1[str(k)]['centre_llenc'], float) for k in POLS}
    def lnG(p):
        x = np.asarray(np.load(p, mmap_mode='r')[..., 1], np.float32); ok = np.isfinite(x) & (x > 0); return np.where(ok, np.log(np.maximum(x, 1e-20)), 0).astype(np.float32), ok
    d3, o3 = lnG(F3 / 'apilats/vixen_total.npy'); d4, o4 = lnG(F4 / 'apilats/vixen_total.npy'); mm = (o3 & o4).astype(np.float32)
    s43 = np.abs(cv2.GaussianBlur((d4 - d3) * mm, (0, 0), 3)); del d3, d4
    n, lab, st, _ = cv2.connectedComponentsWithStats(((s43 > 5e-5) & (mm > 0)).astype(np.uint8), 8); del s43
    PET = {}
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < 300: continue
        x0, y0, w, h = st[i, :4]; c = np.array([x0 + w / 2, y0 + h / 2]); ds = {k: float(np.hypot(*(CEN[k] - c))) for k in POLS}; k = min(ds, key=ds.get)
        if ds[k] > 80: continue
        pad = 120; xa, ya, xb, yb = max(0, x0 - pad), max(0, y0 - pad), min(W, x0 + w + pad), min(H, y0 + h + pad)
        f0 = (lab[ya:yb, xa:xb] == i).astype(np.uint8); f = cv2.dilate(f0, np.ones((31, 31), np.uint8)) > 0
        anell = (cv2.dilate(f.astype(np.uint8), np.ones((181, 181), np.uint8)) > 0) & ~(cv2.dilate(f.astype(np.uint8), np.ones((61, 61), np.uint8)) > 0)
        PET[k] = dict(sl=(slice(ya, yb), slice(xa, xb)), f=f, anell=anell, centre=[int(c[0]), int(c[1])])
    del lab
    CP = {v: np.load(p, mmap_mode='r') for v, p in CMP.items()}
    PARS = [('v4', 'v3'), ('v5', 'v3'), ('v5', 'v4'), ('v4', 'control'), ('v5', 'control'), ('v3', 'control')]
    oA = {}
    for k, p in PET.items():
        sl = p['sl']; X = {v: np.asarray(CP[v][sl], np.float64) for v in CP}; ok = np.logical_and.reduce([np.isfinite(x) & (x > 0) for x in X.values()])
        e = dict(centre=p['centre'], area_px=int(p['f'].sum()))
        for a_, b_ in PARS:
            d = np.where(ok, np.log(np.maximum(X[a_], 1e-12) / np.maximum(X[b_], 1e-12)), 0).astype(np.float32); g = cv2.GaussianBlur(d, (0, 0), 3)
            fi, an = p['f'] & ok, p['anell'] & ok
            e[f'{a_}/{b_}'] = dict(max_abs_G3_pc=round(100 * float(np.abs(g[fi]).max()), 3), rms_G3_pc=round(100 * float(np.sqrt((g[fi].astype(np.float64) ** 2).mean())), 3),
                                   rms_px_pc=round(100 * float(np.sqrt((d[fi].astype(np.float64) ** 2).mean())), 3),
                                   anell_max_abs_G3_pc=round(100 * float(np.abs(g[an]).max()), 3), anell_rms_G3_pc=round(100 * float(np.sqrt((g[an].astype(np.float64) ** 2).mean())), 3))
        oA[str(k)] = e; print('A', k, {q: (e[q]['max_abs_G3_pc'], e[q]['rms_G3_pc']) for q in e if '/' in q}, flush=True)
    R['A_compost_pols_moguda'] = oA; desa()
# ------------------------------------------------------------------------------------------------------------------------------------
# (B) protuberància
# ------------------------------------------------------------------------------------------------------------------------------------
if 'B' in part:
    P1 = json.loads((CAD / 'flat2d_v5/franja/P1_PROTUBERANCIA.json').read_text())
    PX = [(e['x'], e['y'], 'fràgil') for e in P1['fragils']] + [(e['x'], e['y'], 'a tocar del llindar') for e in P1['a_tocar_del_llindar_no_congelats']] + [(4897, 3786, 'veí')]
    Fz = {v: np.load(p) for v, p in FR.items()}; by0, by1, bx0, bx1 = [int(x) for x in Fz['control']['box']]
    cx, cy = 4902, 3782; BX = (slice(cy - 40, cy + 41), slice(cx - 40, cx + 41))
    BG = {v: carrega(BASEG[v], BX) for v in ('control', 'v4', 'v5')}; B16 = {v: carrega(BASE16[v], BX) for v in BASE16}; CPB = {v: carrega(CMP[v], BX) for v in ('control', 'v4', 'v5')}
    FV = {v: {i: (carrega(FILT[v] / f'{TAG[i]}_u16.npy', BX), carrega(FILT[v] / f'{TAG[i]}_alfa_u16.npy', BX)) for i in TAG} for v in FILT}
    def estat_capa(v, i):
        g = ESTAT[v] / f'L{i}_G.npy'; al = ESTAT[v] / f'L{i}_alfa.npy'
        return (carrega(g, BX) if g.exists() else None, carrega(al, BX) if al.exists() else None)
    EV = {v: {i: estat_capa(v, i) for i in TAG} for v in ESTAT}
    L3 = {v: (carrega(ESTAT[v] / 'L3_RGB.npy', BX) if (ESTAT[v] / 'L3_RGB.npy').exists() else None) for v in ESTAT}
    pix = []
    for x, y, tipus in PX:
        yy, xx = y - (cy - 40), x - (cx - 40); fy, fx = y - by0, x - bx0; e = dict(x=x, y=y, tipus=tipus)
        for v in ('control', 'v4', 'v5'):
            q = dict(franja_G=round(float(Fz[v]['G'][fy, fx]), 1), domini_E=bool(Fz[v]['domini_E'][fy, fx]), base_G=round(float(BG[v][yy, xx]), 1),
                     base_u16=np.asarray(B16[v][yy, xx]).round(1).tolist(), compost=round(float(CPB[v][yy, xx]), 5),
                     filtres={i: [int(FV[v][i][0][yy, xx].ravel()[0]) if FV[v][i][0].ndim == 2 else FV[v][i][0][yy, xx].astype(int).tolist(), int(np.asarray(FV[v][i][1][yy, xx]).ravel()[0])] for i in TAG},
                     estat={i: [None if EV[v][i][0] is None else round(float(np.asarray(EV[v][i][0][yy, xx]).ravel()[0]), 1), None if EV[v][i][1] is None else round(float(np.asarray(EV[v][i][1][yy, xx]).ravel()[0]), 1)] for i in TAG},
                     L3_RGB=None if L3[v] is None else np.asarray(L3[v][yy, xx]).round(1).tolist())
            e[v] = q
        e['v5_igual_control'] = dict(base_G=e['v5']['base_G'] == e['control']['base_G'], base_u16=e['v5']['base_u16'] == e['control']['base_u16'], franja_G=e['v5']['franja_G'] == e['control']['franja_G'],
                                     filtres_valor_iguals=[i for i in TAG if e['v5']['filtres'][i][0] == e['control']['filtres'][i][0]], alfes_iguals=all(e['v5']['filtres'][i][1] == e['control']['filtres'][i][1] for i in TAG))
        pix.append(e)
        print('B', x, y, tipus, 'base_G ctl/v4/v5', e['control']['base_G'], e['v4']['base_G'], e['v5']['base_G'], 'compost', e['control']['compost'], e['v4']['compost'], e['v5']['compost'], flush=True)
    # caixa: màxim |ln(v/control)| de la base, de cada capa (valor i alfa) i del compost
    def lnr(a, b):
        ok = (a > 0) & (b > 0) & np.isfinite(a) & np.isfinite(b); return np.where(ok, np.abs(np.log(np.maximum(a, 1e-12) / np.maximum(b, 1e-12))), 0)
    caixa = dict(caixa_xyxy=[cx - 40, cy - 40, cx + 40, cy + 40])
    for v in ('v4', 'v5'):
        o = dict(base_G_max_abs_ln=round(float(lnr(BG[v], BG['control']).max()), 4), base_G_n_px_mes_15pc=int((lnr(BG[v], BG['control']) > 0.15).sum()),
                 base_u16_max_abs_DN=float(np.abs(B16[v].astype(np.float64) - B16['control']).max()), compost_max_abs_ln=round(float(lnr(CPB[v], CPB['control']).max()), 4),
                 compost_n_px_mes_2pc=int((lnr(CPB[v], CPB['control']) > 0.02).sum()), capes={})
        for i in TAG:
            a_, al_ = FV[v][i]; c_, cl_ = FV['control'][i]
            o['capes'][i] = dict(max_abs_ln_valor=round(float(lnr(a_, c_).max()), 4), n_px_valor_mes_5pc=int((lnr(a_, c_) > 0.05).reshape(a_.shape[0], a_.shape[1], -1).any(-1).sum()),
                                 alfa_max_abs_DN=int(np.abs(al_.astype(np.int64) - cl_).max()), n_px_alfa_diferent=int((al_ != cl_).reshape(al_.shape[0], al_.shape[1], -1).any(-1).sum()))
        caixa[f'{v}_sobre_control'] = o
        print('B caixa', v, {k: o[k] for k in o if k != 'capes'}, 'capes: max|ln|', {i: o['capes'][i]['max_abs_ln_valor'] for i in TAG}, 'alfes canviades', {i: o['capes'][i]['n_px_alfa_diferent'] for i in TAG if o['capes'][i]['n_px_alfa_diferent']}, flush=True)
    # la mesura del y3 del verificador: dins del domini de la franja, r = ln(base_v/base_control) per fragilitat
    C_ = Fz['control']; E = C_['E'].astype(np.float64); fr = np.abs(E[..., 1]) / np.maximum(np.abs(E).sum(-1), 1e-9); dom = C_['domini_E']; ok = dom & np.isfinite(fr)
    SLF = (slice(by0, by1), slice(bx0, bx1)); y3 = {}
    for nom, P in (('base_G', BASEG), ('compost', CMP)):
        X = {v: np.asarray(np.load(P[v], mmap_mode='r')[SLF], np.float64) for v in ('control', 'v4', 'v5')}
        for v in ('v4', 'v5'):
            valid = (X['control'] > 0) & (X[v] > 0); r = np.where(valid, np.log(np.maximum(X[v], 1e-12) / np.maximum(X['control'], 1e-12)), np.nan); o = {}
            for lab_, sel in (('f<0.002', ok & (fr < 0.002)), ('f0.002-0.01', ok & (fr >= 0.002) & (fr < 0.01)), ('f>0.01', ok & (fr >= 0.01))):
                rr = r[sel & valid]
                o[lab_] = dict(n=int(rr.size), p50_abs=round(float(np.median(np.abs(rr))), 5), max_abs=round(float(np.abs(rr).max()), 4), n_abs_mes_0_15=int((np.abs(rr) > 0.15).sum()), n_abs_mes_0_5=int((np.abs(rr) > 0.5).sum()))
            y3[f'{nom}_{v}_sobre_control'] = o; print('B y3', nom, v, json.dumps(o), flush=True)
    R['B_protuberancia'] = dict(pixels=pix, caixa=caixa, fragilitat_domini=y3); desa()
# ------------------------------------------------------------------------------------------------------------------------------------
# (C) Brno (còpia del y6 del verificador 4, amb la v5)
# ------------------------------------------------------------------------------------------------------------------------------------
if 'C' in part:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL; del yy, xx
    def lnm(img):
        m = (np.isfinite(img) & (img > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32), m
    bb = sum(np.asarray(np.load(CAD / f'control/estat_v108/L{c}_RGB.npy', mmap_mode='r'), np.float32).mean(-1) for c in (230, 231, 232)) / 3
    lb, mb = lnm(bb); del bb
    IM = {'compost': CMP, 'base': BASEG}; oC = {}
    for nom, ps in IM.items():
        L = {}; m = mb.copy()
        for v, p in ps.items(): L[v], mi = lnm(np.asarray(np.load(p, mmap_mode='r'), np.float32)); m *= mi
        ng = lambda l, s: cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
        res = {}
        for s1, s2 in [(1, 8), (2, 16), (4, 40)]:
            er = int(2 * s2) | 1; okk = (cv2.erode(m, np.ones((er, er), np.uint8)) > 0) & (DL > 3); okk[::2] = False
            db = (ng(lb, s1) - ng(lb, s2)).astype(np.float32); D = {v: (ng(L[v], s1) - ng(L[v], s2)).astype(np.float32) for v in L}; ob = {}
            for r0, r1 in [(1.02, 1.5), (1.5, 2.5)]:
                k = okk & (RS >= r0) & (RS < r1); b = db[k].astype(np.float64); b -= b.mean(); bbn = (b * b).sum(); o = {}
                for v in D:
                    i_ = D[v][k].astype(np.float64); i_ -= i_.mean(); a_ = float((i_ * b).sum() / bbn); rr = float((i_ * b).sum() / np.sqrt(bbn * (i_ * i_).sum())); resta = i_ - a_ * b
                    o[v] = dict(r=round(rr, 4), a=round(a_, 4), E_resta_ppm2=round(1e8 * float((resta ** 2).mean()), 2))
                for v in ('v3', 'v4', 'v5'):
                    o[v]['a_sobre_control'] = round(o[v]['a'] / o['control']['a'], 4); o[v]['E_resta_sobre_control'] = round(o[v]['E_resta_ppm2'] / o['control']['E_resta_ppm2'], 4)
                ob[f'{r0}-{r1}'] = o
            res[f'{s1}-{s2}'] = ob; print('C', nom, s1, s2, json.dumps({rg: {v: (x[v]['r'], x[v].get('E_resta_sobre_control')) for v in x} for rg, x in ob.items()}), f'{time.time()-t0:.0f}s', flush=True); del D, db
        oC[nom] = res; del L
    R['C_brno'] = oC; desa()
# ------------------------------------------------------------------------------------------------------------------------------------
# (D) el compost a les petjades de pols moguda, PER BANDES: rms del DoG σ1–4 i σ4–40 de ln(v/ref) dins de la petjada i a l'anell de fora
#     (30–90 px), per separar la textura fina (que la v5 conserva) del fons de 4–40 px (que la v5 treu)
# ------------------------------------------------------------------------------------------------------------------------------------
if 'D' in part:
    G1 = json.loads((F4 / 'flat2d/G1_PORTA_V4_VIXEN.json').read_text())['grups']['vixen']['decisions']; CEN = {k: np.array(G1[str(k)]['centre_llenc'], float) for k in POLS}
    def lnG(p):
        x = np.asarray(np.load(p, mmap_mode='r')[..., 1], np.float32); ok = np.isfinite(x) & (x > 0); return np.where(ok, np.log(np.maximum(x, 1e-20)), 0).astype(np.float32), ok
    d3, o3 = lnG(F3 / 'apilats/vixen_total.npy'); d4, o4 = lnG(F4 / 'apilats/vixen_total.npy'); mm = (o3 & o4).astype(np.float32)
    s43 = np.abs(cv2.GaussianBlur((d4 - d3) * mm, (0, 0), 3)); del d3, d4
    n, lab, st, _ = cv2.connectedComponentsWithStats(((s43 > 5e-5) & (mm > 0)).astype(np.uint8), 8); del s43
    CP = {v: np.load(p, mmap_mode='r') for v, p in CMP.items()}; oD = {}
    PARS = [('v4', 'v3'), ('v5', 'v3'), ('v5', 'v4'), ('v4', 'control'), ('v5', 'control'), ('v3', 'control')]
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < 300: continue
        x0, y0, w, h = st[i, :4]; c = np.array([x0 + w / 2, y0 + h / 2]); ds = {k: float(np.hypot(*(CEN[k] - c))) for k in POLS}; k = min(ds, key=ds.get)
        if ds[k] > 80: continue
        pad = 260; xa, ya, xb, yb = max(0, x0 - pad), max(0, y0 - pad), min(W, x0 + w + pad), min(H, y0 + h + pad); sl = (slice(ya, yb), slice(xa, xb))
        f = cv2.dilate((lab[sl] == i).astype(np.uint8), np.ones((31, 31), np.uint8)) > 0
        anell = (cv2.dilate(f.astype(np.uint8), np.ones((181, 181), np.uint8)) > 0) & ~(cv2.dilate(f.astype(np.uint8), np.ones((61, 61), np.uint8)) > 0)
        X = {v: np.asarray(CP[v][sl], np.float64) for v in CP}; ok = np.logical_and.reduce([np.isfinite(x) & (x > 0) for x in X.values()]); m = ok.astype(np.float32)
        ng = lambda l, s_: cv2.GaussianBlur(l * m, (0, 0), s_) / np.maximum(cv2.GaussianBlur(m, (0, 0), s_), 1e-6)
        e = dict(centre=[int(c[0]), int(c[1])])
        for a_, b_ in PARS:
            d = np.where(ok, np.log(np.maximum(X[a_], 1e-12) / np.maximum(X[b_], 1e-12)), 0).astype(np.float32); q = {}
            for s1, s2 in ((1, 4), (4, 40)):
                bd = ng(d, s1) - ng(d, s2); fi, an = f & ok, anell & ok
                q[f's{s1}_{s2}'] = dict(rms_dins_1e4=round(1e4 * float(np.sqrt((bd[fi].astype(np.float64) ** 2).mean())), 3), rms_anell_1e4=round(1e4 * float(np.sqrt((bd[an].astype(np.float64) ** 2).mean())), 3))
            e[f'{a_}/{b_}'] = q
        oD[str(k)] = e; print('D', k, {q: (e[q]['s1_4']['rms_dins_1e4'], e[q]['s4_40']['rms_dins_1e4'], e[q]['s4_40']['rms_anell_1e4']) for q in e if '/' in q}, flush=True)
    R['D_compost_pols_moguda_bandes'] = oD; desa()
print('FET', f'{time.time()-t0:.0f}s')
