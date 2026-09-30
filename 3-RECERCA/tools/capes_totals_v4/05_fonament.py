"""05 — Fonament V4: màscares d'ID4, ID5, ID7 = rampa radial solar (lineal suavitzada σ 0,05 R☉) × porta
lunar pròpia (el·lipse mesurada al revelat V4) × (1−P3) [× (1−P4) per a 5 i 7]. Mateix mètode que V3c
(r_a per anell, cerca de Δ per simulació + porta de costura real, DOWN=0 per defecte)."""
import numpy as np
from v4_tests import *
from v4_tests import _P3, _P4

def _pairs(v):
    return [(float(x.split(':')[0]), float(x.split(':')[1]) if ':' in x else 1.0) for x in v.split(',')]

GRID5 = _pairs(os.environ.get('GRID5', '0.5'))
GRID7 = _pairs(os.environ.get('GRID7', '0.7,0.9,1.1'))
DOWN = os.environ.get('DOWN', '0') == '1'
def down(r0, r1):
    return (1 - rampa(RS, r0, r1)) if DOWN else np.float32(1.0)
GATE = {4: (2.0, 10.0), 5: (3.0, 12.0), 7: (3.0, 16.0)}
QA = V4W / 'QA/cerca'
def _occupied(path):
    return path.exists() or path.is_symlink()

_outputs = [V4W / f'states/S{i}.npy' for i in (3, 4, 5, 7)]
_outputs += [V4W / f'masks/mask_{i}.npy' for i in (4, 5, 7)]
_outputs += [V4W / 'QA/fonament_disseny.json']
_existing = [str(path) for path in _outputs if _occupied(path)]
if QA.is_symlink() or (QA.exists() and any(QA.iterdir())):
    _existing.append(str(QA))
if _existing:
    raise SystemExit(f'NO-CLOBBER FONAMENT: ja existeixen outputs: {_existing}')
os.makedirs(QA, exist_ok=True)

def r_snr(i, s):
    return max(r['r'] for r in rang[str(i)] if r['snr'] >= s)

def floor_of(i):
    return float(np.median([r['medG'] for r in rang[str(i)] if r['r'] > 4.3]))

def gate_of(i):
    g, d = lunar_gate_single(ell[str(i)], XX, YY, *GATE[i])
    g[~frame_sel(i)] = 0
    return g

rep = {}
S3 = layer_rgb_canvas(3)
np.save(V4W / 'states/S3.npy', quantize(S3))
g4, g5, g7 = gate_of(4), gate_of(5), gate_of(7)
prot4 = 1 - np.asarray(_P3)
prot57 = prot4 * (1 - np.asarray(_P4))
ra = {}
for i in (4, 5, 7):
    ra[i] = r_a_cells(i)
    print(f'ID{i}: r_a per cel·les = {ra[i][0]} ({ra[i][1]} invàlides); 1r anell vàlid = '
          f'{min([r["r"] for r in rang[str(i)] if r.get("sat_frac",1) <= 0.5 and r.get("snr",0) >= 5] or [None])}', flush=True)
assert ra[4][0] is None, 'la 1/500 hauria de ser vàlida des del limbe'

def search(i, abans_f, r_a, gate, prot, grid):
    Lc = lum(layer_rgb_canvas(i))
    La = lum(abans_f)
    cS, pA, SA = ring_medians(La, RS, 1.0, 4.6, 0.005, SEL, 24, AZS)
    _, pL, SL = ring_medians(Lc, RS, 1.0, 4.6, 0.005, SEL, 24, AZS)
    fl = floor_of(i)
    sim = {}
    res_all = {}
    chosen = None
    for D, wm in grid:
        w = wm * rampa(cS, r_a, r_a + D)
        sim[(D, wm)] = [round(100 * created_rises(cS, pA, pL, w, fl), 3),
                        round(100 * max(created_rises(cS, SA[s], SL[s], w, fl) for s in range(24)), 3)]
        m = np.float32(wm) * rampa(RS, r_a, r_a + D) * gate * prot
        m[~frame_sel(i)] = 0
        mu = quantize(m)
        despres = compose_over(abans_f, i, mu)
        res, _, _ = porta(abans_f, despres, mu, i, Lc, gate, f'{QA}/porta_ID{i}_D{D}_w{wm}.json',
                          extra=dict(r_a=r_a, delta=D, w_max=wm))
        res_all[f'{D}:{wm}'] = dict(D=D, w=wm, veredicte=res['veredicte'], minims_defecte=res['n_minims_defecte'],
                                    V1=len(res['V1_minims_locals_lunar']), empremta=res['empremta_no_radial_rms_pct'], sim=sim[(D, wm)],
                                    pitjors=[dict(p=x['perfil'], r=x['r'], pct=x['prominencia_pct'])
                                             for x in sorted(res['minims'], key=lambda x: -x['prominencia_pct'])[:3]])
        print(f'   ID{i} Δ={D} w={wm}: {res_all[f"{D}:{wm}"]}', flush=True)
        if chosen is None and res['veredicte'] == 'ACCEPTADA':
            chosen = (D, wm)
        del despres
    if chosen is None:
        raise SystemExit(f'ID{i}: cap candidat passa la porta; no se selecciona el menys dolent')
    return chosen, {f'{a}:{b}': v for (a, b), v in sim.items()}, res_all

# ID5 sobre 3+4 (4 provisional amb porta lunar i P3)
m4_tmp = g4 * prot4
m4_tmp[~frame_sel(4)] = 0
S4tmp = compose_over(S3, 4, quantize(m4_tmp))
r_a5 = float(os.environ.get('R_A_5', ra[5][0] if ra[5][0] is not None else
                            min(r['r'] for r in rang['5'] if r.get('sat_frac', 1) <= 0.5 and r.get('snr', 0) >= 5)))
(D5, W5), sim5, res5 = search(5, S4tmp, r_a5, g5, prot57, GRID5)
r_b5 = round(r_a5 + D5, 3)
rd4 = round(max(r_b5 + 0.05, r_snr(4, 5) - 0.20), 3)
rampa4 = (rd4, round(rd4 + 0.20, 3))
m4 = g4 * prot4 * down(*rampa4)
m4[~frame_sel(4)] = 0
M4 = quantize(m4)
S4 = compose_over(S3, 4, M4)
np.save(V4W / 'states/S4.npy', quantize(S4))
up5 = np.float32(W5) * rampa(RS, r_a5, r_b5)
m5_tmp = up5 * g5 * prot57
m5_tmp[~frame_sel(5)] = 0
S5tmp = compose_over(S4, 5, quantize(m5_tmp))
r_a7 = float(os.environ.get('R_A_7', ra[7][0] if ra[7][0] is not None else
                            min(r['r'] for r in rang['7'] if r.get('sat_frac', 1) <= 0.5 and r.get('snr', 0) >= 5)))
(D7, W7), sim7, res7 = search(7, S5tmp, r_a7, g7, prot57, GRID7)
r_b7 = round(r_a7 + D7, 3)
rd5 = round(max(r_b7 + 0.05, r_snr(5, 5) - 0.20), 3)
rampa5 = (rd5, round(rd5 + 0.20, 3))
m5 = up5 * g5 * prot57 * down(*rampa5)
m5[~frame_sel(5)] = 0
M5 = quantize(m5)
S5 = compose_over(S4, 5, M5)
np.save(V4W / 'states/S5.npy', quantize(S5))
rd7 = round(r_snr(7, 5) - 0.20, 3)
rampa7 = (rd7, round(rd7 + 0.25, 3))
m7 = np.float32(W7) * rampa(RS, r_a7, r_b7) * g7 * prot57 * down(*rampa7)
m7[~frame_sel(7)] = 0
M7 = quantize(m7)
S7 = compose_over(S5, 7, M7)
np.save(V4W / 'states/S7.npy', quantize(S7))
masks = {4: M4, 5: M5, 7: M7}
rep = {4: dict(r_a=None, rampa_pujada=None, rampa_baixada=(rampa4 if DOWN else None), r_snr5=r_snr(4, 5),
               porta_lunar=dict(core_px=GATE[4][0], feather_px=GATE[4][1], ellipse=ell['4']), proteccio='(1-P3)'),
       5: dict(r_a=r_a5, delta=D5, w_max=W5, rampa_pujada=(r_a5, r_b5), cerca=res5, rampa_baixada=(rampa5 if DOWN else None),
               r_snr5=r_snr(5, 5), porta_lunar=dict(core_px=GATE[5][0], feather_px=GATE[5][1], ellipse=ell['5']), proteccio='(1-P3)(1-P4)'),
       7: dict(r_a=r_a7, delta=D7, w_max=W7, rampa_pujada=(r_a7, r_b7), cerca=res7, rampa_baixada=(rampa7 if DOWN else None),
               r_snr5=r_snr(7, 5), porta_lunar=dict(core_px=GATE[7][0], feather_px=GATE[7][1], ellipse=ell['7']), proteccio='(1-P3)(1-P4)')}
for i in (4, 5, 7):
    np.save(V4W / 'masks' / f'mask_{i}.npy', masks[i])
    rep[i]['mask_sha256_u16'] = sha256_u16(masks[i])
    rep[i]['mask_max'] = int(masks[i].max())
    d = d_moon(ell[str(i)], XX, YY)
    rep[i]['alpha_max_disc_propi_R+2'] = int(masks[i][d <= R_eq(ell[str(i)]) + 2].max())
    rep[i]['alpha_max_P3'] = int(masks[i][np.asarray(_P3) >= 1].max())
    rep[i]['alpha_max_P4'] = int(masks[i][np.asarray(_P4) >= 1].max()) if i != 4 else None
    print(i, {k: v for k, v in rep[i].items() if k not in ('porta_lunar', 'cerca')}, flush=True)
jdump(rep, V4W / 'QA/fonament_disseny.json')
