"""z2 (verificador adversari 5) · LA PROTUBERÀNCIA A LA v5. Guió propi.
1) Fràgils recalculats: f = |E_G| / Σ|E| de la franja del CONTROL, dins del domini_E del control; quins tenen f < 0,002? Són els 7 de l'autor?
2) La franja de la v5 contra la del control (als congelats, clau a clau) i contra la de la v4 i la de la v5 abans de la regla (franja_a3d de la
   Paperera): quines claus i quins píxels canvien.
3) base_G (lineal), compost i capes 41–56 (_G i alfa, estat de la Paperera) als 7 fràgils, als 2 de la v4 i als 3 «a tocar del llindar».
4) CAP MÉS FRÀGIL FORA DE LA REGLA: a tot el llenç, |ln(base_v/base_control)| (v = v3, v4, v5) fora dels llocs de la pols moguda (M: canvi de la C,
   dilatat 150 px), comptat per classe de fragilitat f_fus = |G|/Σ|RGB| de la fusion_starless del CONTROL (tot el llenç, no només la franja) i
   per f de la franja (dins la caixa). Llista dels pitjors. Nul: el mateix a v3 contra control (el que un flat nou mou normalment).
5) Brno (la mesura y6 del verificador 4, reescrita): base σ1–8 i σ2–16 a 1,02–1,5 R☉, energia de la resta respecte del control, v3/v4/v5.
Sortida: 4-RESULTATS/v108_20260926/verifica5_flat2d/Z2_PROTUBERANCIA.json (només lectura)."""
import json, time
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica5_flat2d'; V8 = A / '4-RESULTATS/v108_20260926'; CAD = V8 / 'cadena'
T4 = Path.home() / '.Trash/Eclipse_V108_flat2d_v4_intermedis_20260927/cadena/flat2d_v4'; T5 = Path.home() / '.Trash/Eclipse_V108_flat2d_v5_intermedis_20260927/cadena/flat2d_v5'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
t0 = time.time(); R = {}
FR = {'control': np.load(CAD / 'control/franja/A3C_franja_silueta.npz'), 'v4': np.load(CAD / 'flat2d_v4/franja/A3C_franja_silueta.npz'),
      'v5': np.load(CAD / 'flat2d_v5/franja/A3C_franja_silueta.npz'), 'v5_abans_regla': np.load(T5 / 'franja_a3d/A3C_franja_silueta.npz')}
by0, by1, bx0, bx1 = [int(x) for x in FR['control']['box']]
C = FR['control']; E = C['E'].astype(np.float64); S = np.abs(E).sum(-1); f = np.where(S > 0, np.abs(E[..., 1]) / np.maximum(S, 1e-9), np.inf)
E5a = FR['v5_abans_regla']['E'].astype(np.float64); S5 = np.abs(E5a).sum(-1); f5 = np.where(S5 > 0, np.abs(E5a[..., 1]) / np.maximum(S5, 1e-9), np.inf)
dom = C['domini_E']
fr = dom & (f < 0.002); ys, xs = np.nonzero(fr)
R['fragils_recalculats'] = sorted([[int(x + bx0), int(y + by0), round(float(f[y, x]), 5)] for y, x in zip(ys, xs)])
R['n_fragils_recalculats'] = int(fr.sum())
for lim in (0.003, 0.005, 0.01):
    k = dom & (f < lim); R[f'n_domini_f_menor_{lim}'] = int(k.sum())
R['a_tocar_min_f'] = sorted([[int(x + bx0), int(y + by0), round(float(f[y, x]), 5), round(float(f5[y, x]), 5)] for y, x in zip(*np.nonzero(dom & ~fr & (np.minimum(f, f5) < 0.002)))])
# fora del domini però a la franja amb f petita (per si la base també en surt)
kk = C['dins_franja'] & ~dom & (f < 0.002)
R['n_dins_franja_fora_domini_f_menor_0_002'] = int(kk.sum())
print('fràgils', R['n_fragils_recalculats'], R['fragils_recalculats'], 'a tocar', R['a_tocar_min_f'], flush=True)
# 2 · claus de la franja
dif = {}
for nom_a, nom_b in (('v5', 'control'), ('v5', 'v4'), ('v5', 'v5_abans_regla'), ('v4', 'control')):
    o = {}
    for k in C.files:
        a, b = FR[nom_a][k], FR[nom_b][k]
        if a.shape != b.shape: o[k] = 'forma diferent'; continue
        d = ~((a == b) | (np.isnan(a) & np.isnan(b)) if a.dtype.kind == 'f' else (a == b))
        if d.ndim == 3: d = d.any(-1)
        if d.ndim == 2:
            n = int(d.sum()); o[k] = n if n == 0 or n > 20 else [[int(x + bx0), int(y + by0)] for y, x in zip(*np.nonzero(d))]
        else: o[k] = int(d.sum())
    dif[f'{nom_a}_contra_{nom_b}'] = o
R['franja_claus_diferents'] = dif
cong = fr | (dom & ~FR['v5_abans_regla']['domini_E'])
R['v5_congelats_iguals_control'] = {k: bool(np.array_equal(FR['v5'][k][cong], C[k][cong])) for k in ('G', 'F', 'V', 'E', 'domini', 'domini_E', 'dins_franja', 'beta')}
print('franja', json.dumps(dif['v5_contra_v4']), json.dumps(R['v5_congelats_iguals_control']), flush=True)
# 3 · valors als píxels
PX = [tuple(p[:2]) for p in R['fragils_recalculats']] + [tuple(p[:2]) for p in R['a_tocar_min_f']]
BG = {'control': CAD / 'control/lineal/base_G.npy', 'v3': CAD / 'flat2d_v3/lineal/base_G.npy', 'v4': CAD / 'flat2d_v4/lineal/base_G.npy', 'v5': CAD / 'flat2d_v5/lineal/base_G.npy'}
CMP = {'control': V8 / 'flat2d_v2/compost_control.npy', 'v3': V8 / 'flat2d_v3/compost_flat2d_v3.npy', 'v4': V8 / 'flat2d_v4/compost_flat2d_v4.npy', 'v5': V8 / 'flat2d_v5/compost_flat2d_v5.npy'}
EST = {'control': CAD / 'control/estat_v108', 'v4': T4 / 'estat_v108', 'v5': T5 / 'estat_v108'}
BGm = {v: np.load(p, mmap_mode='r') for v, p in BG.items()}; CPm = {v: np.load(p, mmap_mode='r') for v, p in CMP.items()}
pix = []
for x, y in PX:
    e = dict(x=x, y=y, f_control=round(float(f[y - by0, x - bx0]), 5), base_G={v: round(float(BGm[v][y, x]), 1) for v in BGm}, compost={v: round(float(CPm[v][y, x]), 5) for v in CPm},
             franja_G={v: round(float(FR[v]['G'][y - by0, x - bx0]), 1) for v in FR})
    e['base_v5_igual_control'] = bool(BGm['v5'][y, x] == BGm['control'][y, x]); e['compost_v5_sobre_control_pc'] = round(100 * float(CPm['v5'][y, x] / CPm['control'][y, x] - 1), 3)
    e['compost_v4_sobre_control_pc'] = round(100 * float(CPm['v4'][y, x] / CPm['control'][y, x] - 1), 3)
    pix.append(e)
# capes 41–56 als píxels i alfes a la caixa 81×81
cy, cx = 3781, 4903; cap = {}; alf = {}
for L in range(41, 57):
    Gm = {v: np.load(EST[v] / f'L{L}_G.npy', mmap_mode='r') for v in EST}; Am = {v: np.load(EST[v] / f'L{L}_alfa.npy', mmap_mode='r') for v in EST}
    for e in pix: e.setdefault('capes', {})[L] = {v: float(Gm[v][e['y'], e['x']]) for v in Gm}
    alf[L] = {v: bool(np.array_equal(np.asarray(Am[v][cy - 40:cy + 41, cx - 40:cx + 41]), np.asarray(Am['control'][cy - 40:cy + 41, cx - 40:cx + 41]))) for v in ('v4', 'v5')}
R['pixels'] = pix; R['alfes_41_56_caixa81_iguals_control'] = alf
print('píxels', json.dumps([(e['x'], e['y'], e['base_G'], e['compost_v5_sobre_control_pc'], e['compost_v4_sobre_control_pc']) for e in pix]), flush=True)
print('alfes', json.dumps(alf), flush=True)
(OUT / 'Z2_PROTUBERANCIA.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
# 4 · cap més fràgil fora de la regla: tot el llenç
cC = np.load(V8 / 'flat2d_v5/flat2d/VIXEN_flat2d_v5.npz')['C']; cC4 = np.load(V8 / 'flat2d_v4/flat2d/VIXEN_flat2d_v4.npz')['C']
R['C_vixen_px_diferents_raw'] = int((cC != cC4).sum()); del cC, cC4
# llocs de la pols: canvi de l'apilat de la Vixen v5 − v4, dilatat 150 px
a = np.asarray(np.load(V8 / 'flat2d_v4/apilats/vixen_total.npy', mmap_mode='r')[..., 1], np.float32); b = np.asarray(np.load(V8 / 'flat2d_v5/apilats/vixen_total.npy', mmap_mode='r')[..., 1], np.float32)
M = ~((a == b) | (np.isnan(a) & np.isnan(b))); del a, b
M = cv2.dilate(M.astype(np.uint8), np.ones((301, 301), np.uint8)) > 0
fus = np.load(CAD / 'control/lineal/fusion_starless.npy', mmap_mode='r')
ffus = np.full((H, W), np.inf, np.float32)
for y0 in range(0, H, 1000):
    x = np.asarray(fus[y0:y0 + 1000], np.float64); s = np.abs(x).sum(-1); ffus[y0:y0 + 1000] = np.where(s > 0, np.abs(x[..., 1]) / np.maximum(s, 1e-9), np.inf)
del fus
bc = np.asarray(BGm['control'], np.float32)
fbox = np.full((H, W), np.inf, np.float32); fbox[by0:by1, bx0:bx1] = f
for v in ('v3', 'v4', 'v5'):
    bv = np.asarray(BGm[v], np.float32); ok = np.isfinite(bv) & np.isfinite(bc) & (bv > 0) & (bc > 0)
    r = np.where(ok, np.log(np.maximum(bv, 1e-20) / np.maximum(bc, 1e-20)), 0).astype(np.float32); del bv
    o = {}
    for nom, sel in (('f_fus<0.002', ffus < 0.002), ('f_fus0.002-0.005', (ffus >= 0.002) & (ffus < 0.005)), ('f_fus0.005-0.02', (ffus >= 0.005) & (ffus < 0.02)), ('f_fus>=0.02', ffus >= 0.02)):
        k = sel & ok & ~M
        if k.sum() == 0: o[nom] = dict(n=0); continue
        x = np.abs(r[k]); o[nom] = dict(n=int(k.sum()), p50=round(float(np.median(x)), 6), p99=round(float(np.percentile(x, 99)), 5), max=round(float(x.max()), 4), n_mes_0_15=int((x > 0.15).sum()), n_mes_0_05=int((x > 0.05).sum()))
    k = ok & ~M & (np.abs(r) > 0.05); ys, xs = np.nonzero(k); ordre = np.argsort(-np.abs(r[ys, xs]))[:25]
    o['pitjors_fora_llocs_mes_0_05'] = [dict(x=int(xs[i]), y=int(ys[i]), r=round(float(r[ys[i], xs[i]]), 4), f_fus=round(float(ffus[ys[i], xs[i]]), 5), f_franja=round(float(fbox[ys[i], xs[i]]), 5) if np.isfinite(fbox[ys[i], xs[i]]) else None,
                                            dL=round(float(np.hypot(xs[i] - LLUNA[0], ys[i] - LLUNA[1]) - RL), 1), control=round(float(bc[ys[i], xs[i]]), 1)) for i in ordre]
    o['n_fora_llocs_mes_0_05'] = int(k.sum()); o['n_fora_llocs_mes_0_15'] = int((ok & ~M & (np.abs(r) > 0.15)).sum())
    # dins la caixa de la franja, per f de la franja (domini i fora)
    rb = r[by0:by1, bx0:bx1]; okb = ok[by0:by1, bx0:bx1]
    for nom, sel in (('franja_domini_f<0.002', dom & (f < 0.002)), ('franja_domini_f0.002-0.005', dom & (f >= 0.002) & (f < 0.005)), ('franja_domini_f>=0.005', dom & (f >= 0.005)),
                     ('franja_fora_domini_f<0.005', ~dom & (f < 0.005)), ('caixa_fora_domini', ~dom)):
        kk2 = sel & okb
        if kk2.sum() == 0: o[nom] = dict(n=0); continue
        x = np.abs(rb[kk2]); o[nom] = dict(n=int(kk2.sum()), p50=round(float(np.median(x)), 6), max=round(float(x.max()), 4), n_mes_0_15=int((x > 0.15).sum()))
    R[f'base_G_{v}_sobre_control'] = o; del r
    print(v, json.dumps({kk_: vv for kk_, vv in o.items() if not kk_.startswith('pitjors')}), f'{time.time()-t0:.0f}s', flush=True)
    (OUT / 'Z2_PROTUBERANCIA.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
del bc, ffus, fbox
# 5 · Brno a la base
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL; del yy, xx
def lnm(img):
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32), m
bb = sum(np.asarray(np.load(CAD / f'control/estat_v108/L{c}_RGB.npy', mmap_mode='r'), np.float32).mean(-1) for c in (230, 231, 232)) / 3
lb, mb = lnm(bb); del bb
L = {}; m = mb.copy()
for v, p in BG.items():
    L[v], mi = lnm(np.asarray(np.load(p, mmap_mode='r'), np.float32)); m *= mi
ng = lambda l, s: cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
RB = {}
for s1, s2 in ((1, 8), (2, 16)):
    er = int(2 * s2) | 1; ok = (cv2.erode(m, np.ones((er, er), np.uint8)) > 0) & (DL > 3); ok[::2] = False
    db = (ng(lb, s1) - ng(lb, s2)).astype(np.float32); k = ok & (RS >= 1.02) & (RS < 1.5)
    b = db[k].astype(np.float64); b -= b.mean(); bbn = (b * b).sum(); o = {}
    for v in L:
        i = (ng(L[v], s1) - ng(L[v], s2))[k].astype(np.float64); i -= i.mean(); a_ = float((i * b).sum() / bbn); rr = float((i * b).sum() / np.sqrt(bbn * (i * i).sum()))
        o[v] = dict(r=round(rr, 4), a=round(a_, 4), E_resta=float(((i - a_ * b) ** 2).mean()))
    for v in ('v3', 'v4', 'v5'): o[v]['E_resta_sobre_control'] = round(o[v]['E_resta'] / o['control']['E_resta'], 4)
    RB[f'{s1}-{s2}'] = o; print('Brno base', s1, s2, json.dumps({v: (o[v]['r'], o[v].get('E_resta_sobre_control')) for v in o}), flush=True)
R['brno_base_1.02-1.5'] = RB
(OUT / 'Z2_PROTUBERANCIA.json').write_text(json.dumps(R, ensure_ascii=False, indent=1)); print('FET', f'{time.time()-t0:.0f}s')
