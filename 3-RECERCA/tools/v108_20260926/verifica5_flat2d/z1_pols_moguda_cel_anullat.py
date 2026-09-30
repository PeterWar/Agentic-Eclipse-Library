"""z1 (verificador adversari 5) · LA POLS MOGUDA DE LA v5: el que la v5 treu de la v4 i el que hi deixa, és cura? Guió propi.
Petjades pròpies: el CANVI v5 − v4 de l'apilat de la Vixen (canal G), |G3| > 5·10⁻⁵, components ≥ 300 px, dilatades 15 px. No es llegeix cap
fitxer de l'autor per definir-les. Es comprova que en surten 5 i que cauen sobre els 5 centres de l'encàrrec.
Cel anul·lat: Z_v = ln V_v − S, S = mitjana de ln A i ln B de la Sony del CONTROL (fixa per a totes les variants: Δ_Z = Δ_V).
Bandes DoG normalitzades a la màscara comuna: σ1–4, σ4–40, σ10–60.
  s = (|X + D|² − |X|²)/|D|², X = banda de Z de la variant de partida, D = banda del canvi. −1 = cura exacta; +1 = com el nul.
  p_v = ⟨Z_v, D43⟩/|D43|², D43 = banda de (v4 − v3): «la dada que queda en la direcció del canvi de la v4» (p_v4 − p_v3 = 1 per construcció).
NUL a la mateixa imatge: 24 desplaçaments de 450–1200 px (llavor 7373, diferent de la de l'autor i del verificador 4), fora de qualsevol petjada
(v4 − v3 dels tres apilats, dilatada 61 px) i de la vora.
Compost (control, v3, v4, v5): a cada petjada, rms de la banda σ4–40 i σ1–4 de ln(v/v3) i màxim |G3 ln(v/v3)|.
Sortida: 4-RESULTATS/v108_20260926/verifica5_flat2d/Z1_POLS_MOGUDA.json (només lectura; ~10 GB)."""
import json, time
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica5_flat2d'
W, H = 10551, 7506; LLUNA = (5375.787, 3775.977); RL = 452.98
CR = A / '4-RESULTATS/v97_refundacio_20260924'; V8 = A / '4-RESULTATS/v108_20260926'
F = {v: V8 / f'flat2d_{v}' for v in ('v3', 'v4', 'v5')}
AP = {'control': dict(V=CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', A=CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', B=CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy')}
for v in ('v3', 'v4', 'v5'): AP[v] = dict(V=F[v] / 'apilats/vixen_total.npy', A=F[v] / 'apilats/sony_A_total.npy', B=F[v] / 'apilats/cau/sony_B_total_v42.npy')
CMP = {'control': V8 / 'flat2d_v2/compost_control.npy', 'v3': F['v3'] / 'compost_flat2d_v3.npy', 'v4': F['v4'] / 'compost_flat2d_v4.npy', 'v5': F['v5'] / 'compost_flat2d_v5.npy'}
ENC = [(5860, 5354), (2864, 2088), (3898, 2503), (6408, 4793), (6149, 4386)]
t0 = time.time()
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL; del yy, xx
def lnG(p):
    x = np.asarray(np.load(p, mmap_mode='r')[..., 1], np.float32); ok = np.isfinite(x) & (x > 0)
    return np.where(ok, np.log(np.maximum(x, 1e-20)), 0).astype(np.float32), ok
R = {}
# 1 · petjades pròpies: canvi v5 − v4 de la Vixen
v4, o4 = lnG(AP['v4']['V']); v5, o5 = lnG(AP['v5']['V']); m = (o4 & o5)
d54 = np.where(m, v5 - v4, 0).astype(np.float32)
R['vixen_v5_menys_v4_px_diferents'] = int((d54 != 0).sum())
s54 = np.abs(cv2.GaussianBlur(d54, (0, 0), 3)); del v4, v5, d54
z = (s54 > 5e-5).astype(np.uint8); n, lab, st, cen = cv2.connectedComponentsWithStats(z, 8)
PET = []; TOTF = np.zeros((H, W), bool)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] < 300: continue
    x0, y0, w, h = st[i, :4]; pad = 24; xa, ya, xb, yb = max(0, x0 - pad), max(0, y0 - pad), min(W, x0 + w + pad), min(H, y0 + h + pad)
    f0 = (lab[ya:yb, xa:xb] == i).astype(np.uint8); f = cv2.dilate(f0, np.ones((31, 31), np.uint8)) > 0
    c = cen[i]; dd = [float(np.hypot(c[0] - e[0], c[1] - e[1])) for e in ENC]; j = int(np.argmin(dd))
    PET.append(dict(xa=int(xa), ya=int(ya), f=f, centre=[round(float(c[0]), 1), round(float(c[1]), 1)], area=int(st[i, cv2.CC_STAT_AREA]), encarrec=list(ENC[j]), dist_encarrec=round(dd[j], 1)))
    TOTF[ya:yb, xa:xb] |= f
R['petjades_v5_menys_v4'] = [{k: v for k, v in p.items() if k not in ('f', 'xa', 'ya')} for p in PET]
R['n_components_petits_menys_300px'] = int(sum(1 for i in range(1, n) if st[i, cv2.CC_STAT_AREA] < 300))
print('petjades', R['petjades_v5_menys_v4'], f'{time.time()-t0:.0f}s', flush=True); del s54, lab, z
# exclusió dels nuls: canvi v4 − v3 dels tres apilats
EXC = TOTF.copy()
for k in ('A', 'B', 'V'):
    a, oa = lnG(AP['v3'][k]); b, ob = lnG(AP['v4'][k]); d = np.where(oa & ob, b - a, 0).astype(np.float32); del a, b
    EXC |= np.abs(cv2.GaussianBlur(d, (0, 0), 3)) > 5e-5; del d
EXC = cv2.dilate(EXC.astype(np.uint8), np.ones((61, 61), np.uint8)) > 0
rng = np.random.default_rng(7373); DESPL = []
while len(DESPL) < 24:
    r_ = rng.uniform(450, 1200); t_ = rng.uniform(0, 2 * np.pi); DESPL.append((int(r_ * np.cos(t_)), int(r_ * np.sin(t_))))
R['desplacaments'] = DESPL; R['llavor'] = 7373
# 2 · Z amb el cel anul·lat
a, oa = lnG(AP['control']['A']); b, ob = lnG(AP['control']['B']); S = np.where(oa & ob, 0.5 * (a + b), np.where(oa, a, b)).astype(np.float32); oS = oa | ob; del a, b, oa, ob
Z = {}; okz = oS.copy()
for v in ('control', 'v3', 'v4', 'v5'):
    a, oa = lnG(AP[v]['V']); Z[v] = np.where(oa & oS, a - S, 0).astype(np.float32); okz &= oa; del a, oa
del S
mk = (okz & (DL > 40)).astype(np.float32); okb = cv2.erode(mk, np.ones((121, 121), np.uint8)) > 0; okn = okb & ~EXC
def ng(x, s): return cv2.GaussianBlur(x * mk, (0, 0), s) / np.maximum(cv2.GaussianBlur(mk, (0, 0), s), 1e-6)
CANVIS = [('v5_menys_v4', 'v4', 'v5'), ('v5_menys_v3', 'v3', 'v5'), ('v4_menys_v3', 'v3', 'v4'), ('v5_menys_control', 'control', 'v5'), ('v4_menys_control', 'control', 'v4'), ('v3_menys_control', 'control', 'v3')]
for sa, sb in ((1, 4), (4, 40), (10, 60)):
    Bd = {v: (ng(Z[v], sa) - ng(Z[v], sb)).astype(np.float32) for v in Z}
    out = {}
    for nomc, va, vb in CANVIS:
        tot = dict(num=0.0, den=0.0, nn=np.zeros(24), dd=np.zeros(24)); per = []
        for p in PET:
            f = p['f']; h, w = f.shape; ya, xa = p['ya'], p['xa']; fv = f & okb[ya:ya + h, xa:xa + w]
            if fv.sum() < 200: continue
            X = Bd[va][ya:ya + h, xa:xa + w][fv].astype(np.float64); D = Bd[vb][ya:ya + h, xa:xa + w][fv].astype(np.float64) - X
            ed = (D ** 2).sum(); num = ((X + D) ** 2).sum() - (X ** 2).sum(); nn = np.full(24, np.nan)
            for j, (dx, dy) in enumerate(DESPL):
                y2, x2 = ya + dy, xa + dx
                if y2 < 0 or x2 < 0 or y2 + h > H or x2 + w > W or not okn[y2:y2 + h, x2:x2 + w][fv].all(): continue
                Xs = Bd[va][y2:y2 + h, x2:x2 + w][fv].astype(np.float64); nn[j] = ((Xs + D) ** 2).sum() - (Xs ** 2).sum()
            ok_ = np.isfinite(nn); tot['num'] += num; tot['den'] += ed; tot['nn'][ok_] += nn[ok_]; tot['dd'][ok_] += ed
            sn = nn[ok_] / ed
            per.append(dict(encarrec=p['encarrec'], s=round(num / ed, 3), s_nul=round(float(sn.mean()), 3) if sn.size > 3 else None, s_nul_sd=round(float(sn.std()), 3) if sn.size > 3 else None, n_nul=int(sn.size),
                            rms_canvi_1e4=round(1e4 * float(np.sqrt(ed / fv.sum())), 3)))
        okj = tot['dd'] > 0; sn = tot['nn'][okj] / tot['dd'][okj]
        out[nomc] = dict(s_5=round(tot['num'] / tot['den'], 3), s_nul=round(float(sn.mean()), 3), s_nul_sd=round(float(sn.std()), 3), n_nul=int(okj.sum()),
                         z=round(float((tot['num'] / tot['den'] - sn.mean()) / sn.std()), 2), per_petjada=per)
        print(f'σ{sa}–{sb}', nomc, out[nomc]['s_5'], out[nomc]['s_nul'], '±', out[nomc]['s_nul_sd'], f'{time.time()-t0:.0f}s', flush=True)
    # projecció sobre D43
    proj = {v: 0.0 for v in Z}; den = 0.0; projp = []
    for p in PET:
        f = p['f']; h, w = f.shape; ya, xa = p['ya'], p['xa']; fv = f & okb[ya:ya + h, xa:xa + w]
        if fv.sum() < 200: continue
        D = Bd['v4'][ya:ya + h, xa:xa + w][fv].astype(np.float64) - Bd['v3'][ya:ya + h, xa:xa + w][fv]; e = (D ** 2).sum(); den += e
        pp = {}
        for v in Z:
            q = float((Bd[v][ya:ya + h, xa:xa + w][fv].astype(np.float64) * D).sum()); proj[v] += q; pp[v] = round(q / e, 3)
        projp.append(dict(encarrec=p['encarrec'], **pp))
    # nul de la projecció: la dada del control a la posició desplaçada projectada sobre D43
    pn = []
    for j, (dx, dy) in enumerate(DESPL):
        q = 0.0; e_ = 0.0
        for p in PET:
            f = p['f']; h, w = f.shape; ya, xa = p['ya'], p['xa']; fv = f & okb[ya:ya + h, xa:xa + w]; y2, x2 = ya + dy, xa + dx
            if fv.sum() < 200 or y2 < 0 or x2 < 0 or y2 + h > H or x2 + w > W or not okn[y2:y2 + h, x2:x2 + w][fv].all(): continue
            D = Bd['v4'][ya:ya + h, xa:xa + w][fv].astype(np.float64) - Bd['v3'][ya:ya + h, xa:xa + w][fv]
            q += float((Bd['control'][y2:y2 + h, x2:x2 + w][fv].astype(np.float64) * D).sum()); e_ += (D ** 2).sum()
        if e_ > 0: pn.append(q / e_)
    out['projeccio_sobre_v4_menys_v3'] = dict(**{v: round(proj[v] / den, 3) for v in Z}, nul_mitjana=round(float(np.mean(pn)), 3), nul_sd=round(float(np.std(pn)), 3), n_nul=len(pn), per_petjada=projp)
    print(f'σ{sa}–{sb}', 'projecció', {v: out['projeccio_sobre_v4_menys_v3'][v] for v in Z}, 'nul', out['projeccio_sobre_v4_menys_v3']['nul_mitjana'], '±', out['projeccio_sobre_v4_menys_v3']['nul_sd'], flush=True)
    R[f'banda_{sa}_{sb}'] = out; del Bd
    (OUT / 'Z1_POLS_MOGUDA.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
del Z
# 3 · compost
L = {}; ok = np.ones((H, W), bool)
for v, pth in CMP.items():
    x = np.asarray(np.load(pth, mmap_mode='r'), np.float32); o = np.isfinite(x) & (x > 0); ok &= o; L[v] = np.log(np.maximum(np.where(o, x, 1), 1e-20)).astype(np.float32); del x
mk = ok.astype(np.float32)
def band(d, sa, sb): return (ng(d, sa) - ng(d, sb)).astype(np.float32)
RC = {}
for v in ('v4', 'v5', 'control'):
    d = np.where(ok, L[v] - L['v3'], 0).astype(np.float32); b440 = band(d, 4, 40); b14 = band(d, 1, 4); g3 = cv2.GaussianBlur(d * mk, (0, 0), 3) / np.maximum(cv2.GaussianBlur(mk, (0, 0), 3), 1e-6)
    for p in PET:
        f = p['f']; h, w = f.shape; ya, xa = p['ya'], p['xa']; fv = f & ok[ya:ya + h, xa:xa + w]
        e = RC.setdefault(str(p['encarrec']), {})
        e[f'{v}_sobre_v3'] = dict(rms_s4_40_1e4=round(1e4 * float(np.sqrt((b440[ya:ya + h, xa:xa + w][fv].astype(np.float64) ** 2).mean())), 2),
                                  rms_s1_4_1e4=round(1e4 * float(np.sqrt((b14[ya:ya + h, xa:xa + w][fv].astype(np.float64) ** 2).mean())), 2),
                                  max_abs_G3_pc=round(100 * float(np.abs(g3[ya:ya + h, xa:xa + w][fv]).max()), 3))
    del d, b440, b14, g3
R['compost'] = RC; print('compost', json.dumps(RC), flush=True)
(OUT / 'Z1_POLS_MOGUDA.json').write_text(json.dumps(R, ensure_ascii=False, indent=1)); print('FET', f'{time.time()-t0:.0f}s')
