"""Cadena ID8 → ID9 → ID10: per a cada capa, r_a (primer anell vàlid), r_b (amplada de transició per simulació de
monotonia del perfil), màscara = smootherstep(r) × porta de banda lunar × PF, composició, porta i pilots.
Ús: disseny.py <dir_QA> [ids...]"""
import sys, json, os, numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks
from v3b_lib import *
from geom import ELL, R_moon, member_centres
QA = sys.argv[1]; os.makedirs(QA, exist_ok=True)
ids = [int(s) for s in sys.argv[2:]] or [8, 9, 10]
MASKDIR = f'{V3B}/masks'; os.makedirs(MASKDIR, exist_ok=True)
rang = json.load(open(f'{V3B}/rang.json'))
xx, yy = canvas_grid(); rs = r_sun_canvas(xx, yy)
azs = np.degrees(np.arctan2(-(yy-SUN[1]), xx-SUN[0])) % 360
l, t, r_, b = FRAME; sel = np.zeros((CH, CW), bool); sel[t:b, l:r_] = True
print('PF (protecció P3/P4 des de la màscara d\'ID7 de Corretgint2)...', flush=True)
pf, pf_info = protection_factor(xx, yy)
np.save(f'{V3B}/pf.npy', pf)
print(f'   PF<1 en {(pf < 0.999).sum()} px; PF==0 en {(pf == 0).sum()} px', flush=True)
abans = np.asarray(load_abans_rgb()[..., :3], np.float32)/65535.
state = 'v2b'
if os.environ.get('ABANS_NPY'):
    abans = np.asarray(np.load(os.environ['ABANS_NPY'], mmap_mode='r'), np.float32)/65535.; state = os.environ.get('ABANS_STATE', 'custom')
receipt = {}
def layer_getter(i):
    R_, G_, B_ = load_layer_rgb(i)
    def get(y0, y1, x0, x1):
        out = np.zeros((y1-y0, x1-x0, 3), np.float32)
        ly0, ly1 = max(y0, t), min(y1, b); lx0, lx1 = max(x0, l), min(x1, r_)
        if ly1 > ly0 and lx1 > lx0:
            for k, ch in enumerate((R_, G_, B_)):
                out[ly0-y0:ly1-y0, lx0-x0:lx1-x0, k] = np.asarray(ch[ly0-t:ly1-t, lx0-l:lx1-l], np.float32)/65535.
        return out
    return get
for i in ids:
    print(f'== ID{i}', flush=True)
    rows = rang[str(i)]
    valid = [row['r'] for row in rows if row['p50'] <= 0.46 and row['p95'] <= 0.66]
    r_a_valid = float(min(valid)); r_a = float(os.environ.get(f'R_A_{i}', r_a_valid))  # entrada posposada admesa (més conservadora)
    # perfils de mediana (lum) d'ABANS i de la capa, global i 24 sectors, 0,005 R☉
    La = lum(abans)
    Lc = np.zeros((CH, CW), np.float32)
    get = layer_getter(i); Lc[t:b, l:r_] = lum(get(t, b, l, r_))
    cS, pA, SA = ring_medians(La, rs, 1.0, 4.6, 0.005, sel, 24, azs)
    _, pL, SL = ring_medians(Lc, rs, 1.0, 4.6, 0.005, sel, 24, azs)
    # mesura del solapament: anells on la capa és vàlida i la inferior encara hi és (lum > 2x el seu terra)
    floor_A = float(np.nanmedian(pA[(cS > 4.3)])); floor_L = float(np.nanmedian(pL[(cS > 4.3)]))
    # simulació: r_b mínim amb perfil compost monòton (global i a 24 sectors), prominència de mínim < 0,2 %
    def simula(r_b, wm=1.0):
        w = wm*rampa(cS, r_a, r_b)
        worst = created_rises(cS, pA, pL, w, floor_L)
        per_sector = sorted(created_rises(cS, SA[s], SL[s], w, floor_L) for s in range(24))
        return worst, per_sector[-1]
    # Les capes no estan normalitzades per exposició (q = capa/compost ≈ 2 a ID8/ID9 i ≈ 4 a ID10) i el compost de sota
    # baixa només 1–3 /R☉ més enllà d'1,5 R☉: cap rampa a pes 1 no manté el perfil monòton als sectors foscos. El pes
    # màxim w_max és, doncs, part del disseny (R11: dins del rang la màscara és pes). Cerca (Δ, w_max): el w_max més
    # gran amb pujada creada global < 0,2 % i pitjor sector < 1 %, amb Δ ≤ 0,7 R☉; empat → Δ més petit.
    r_lin = min([row['r'] for row in rows if row['p50'] <= 0.20 and row['r'] >= r_a] or [r_a+0.25])
    sim = {}; best = None
    for D in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
        if r_a + D < r_lin: continue
        for wm in np.round(np.arange(1.0, 0.19, -0.05), 2):
            g, sw = simula(r_a+D, wm); sim[f'D={D}_w={wm}'] = [round(100*g, 3), round(100*sw, 3)]
            # la porta real surt ~1,5x la simulació: llindar de sector 0,5 % perquè el real quedi sota l'1 %
            if g < 0.002 and sw < 0.005 and (best is None or wm > best[1]): best = (D, float(wm))
    if best is None: best = (0.7, 0.2)
    D, w_max = best; r_b = round(r_a + D, 3); r_b_min = r_b; g_rb, s3_rb = simula(r_b, w_max)
    print(f'   r_a={r_a} R☉ ({r_a*R_SUN:.0f} px del Sol); r_b={r_b} (amplada {(r_b-r_a)*R_SUN:.0f} px), w_max={w_max}; pujada creada simulada: global {100*g_rb:.3f} %, pitjor sector {100*s3_rb:.3f} %; r_lin={r_lin}', flush=True)
    # màscara
    prof = np.float32(w_max)*rampa(rs, r_a, r_b)
    gate_l, dmin = band_gate(i, xx, yy)
    alpha = prof*gate_l*pf; alpha[~sel] = 0
    m7 = np.asarray(np.load(f'{V3B}/src_id7_mask.npy', mmap_mode='r'))
    d7 = np.hypot(xx-MOON7_C2[0], yy-MOON7_C2[1])
    hard0 = (m7 == 0) & (d7 <= 620)
    alpha[hard0] = 0
    alpha_u16 = quantize(alpha)
    mpath = f'{MASKDIR}/mask_{i}.npy'; np.save(mpath, alpha_u16)
    msha = sha256_u16(alpha_u16)
    ref, cs = member_centres(i)
    despres = compose(abans, i, alpha_u16)
    res, Qa, Qd = gate(abans, despres, alpha_u16, i, pf, xx, yy, f'{QA}/porta_ID{i}.json', layer_lum=Lc,
                       extra=dict(r_a_rsun=r_a, r_a_primer_anell_valid_rsun=r_a_valid, r_b_rsun=r_b, w_max=w_max, r_lin_rsun=r_lin, amplada_px=round((r_b-r_a)*R_SUN, 1), rampa='lineal r_a→r_b suavitzada σ 0,05 R☉', simulacio_pujada_creada_pct=sim, pujada_creada_adoptada_pct=[round(100*g_rb, 3), round(100*s3_rb, 3)],
                                  porta_lunar=dict(tipus='zero on qualsevol membre té disc+marge+transició (478 px del seu centre); ploma radial smootherstep 20 px',
                                                   centres_membres_llenç={f: [round(a+OFF[0], 2), round(bb+OFF[1], 2), round(dt, 2)] for f, (a, bb, dt) in cs.items()},
                                                   R_equiv_px=round(R_moon(i), 2), ellipse=ELL[str(i)], extensio_max_px=round(float(BAND_R+max(np.hypot(a-cs[ref][0], bb-cs[ref][1]) for f, (a, bb, dt) in cs.items())-R_moon(i)), 1)),
                                  mask_sha256_u16=msha, mask_path=mpath, mask_max=int(alpha_u16.max()), pf_zero_px=int((pf == 0).sum()), hard0_px=int(hard0.sum()),
                                  abans=state))
    # pilots 1:1
    cxm, cym = moon_centre_canvas(i)
    ang = np.radians(150); pa_ = (cxm+470*np.cos(ang), cym-470*np.sin(ang))
    r_mid = 0.5*(r_a+r_b)*R_SUN
    pts = {'a_limbe_banda_150deg': pa_, 'b_protuberancia_P4': (3578, 2653),
           'c1_costura_45deg': (SUN[0]+r_mid*np.cos(np.radians(45)), SUN[1]-r_mid*np.sin(np.radians(45))),
           'c2_costura_225deg': (SUN[0]+r_mid*np.cos(np.radians(225)), SUN[1]-r_mid*np.sin(np.radians(225)))}
    pil = {}
    for k, (px, py) in pts.items():
        pil[k] = pilot_crop(abans, despres, get, alpha_u16, px, py, f'{QA}/pilot_ID{i}_{k}.png', title=f'ID{i} {k}')
    overview(despres, f'{QA}/compost_ID{i}_1de4.png')
    res['pilots'] = pil
    json.dump(res, open(f'{QA}/porta_ID{i}.json', 'w'), indent=1)
    print(f"   porta: {res['veredicte']} | mínims defecte={res['n_minims_defecte']} (nous reportats {res['n_minims_nous_reportats']}) | empremta no radial {res['empremta_no_radial_rms_pct']} % (amb portes {res['empremta_no_radial_rms_pct_inclou_portes']} %) | nuclis dif {res['nuclis_P3P4_dif_max_DN']} DN α {res['nuclis_P3P4_alpha_max']} | fora suport dif {res['fora_suport_dif_max_DN']} | V1 mínims {len(res['V1_minims_locals_lunar'])} | discs α max {max(v['alpha_max'] for v in res['discs_lunars'].values())}", flush=True)
    for m in res['minims']:
        if m['defecte'] or (m['nou'] and m['prominencia_pct'] >= 1.0): print('     mínim nou:', m)
    receipt[i] = dict(veredicte=res['veredicte'], r_a=r_a, r_b=r_b, w_max=w_max, mask_sha256_u16=msha)
    if res['veredicte'] == 'ACCEPTADA':
        abans = despres; state = state + f'+{i}'
        np.save(f'{V3B}/compost_after_{i}.npy', Qd)
    else:
        del despres
json.dump(receipt, open(f'{QA}/cadena.json', 'w'), indent=1)
print(json.dumps(receipt, indent=1))
