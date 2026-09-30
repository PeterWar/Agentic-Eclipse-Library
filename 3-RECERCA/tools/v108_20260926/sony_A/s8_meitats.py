"""s8 · APILATS PER MEITATS TEMPORALS de cada apuntament de la Sony (A1: t ≤ 18 s, A2: t ≥ 28 s; B1: t ≤ 70 s, B2: t ≥ 80 s), amb el flat 2D
del pilot i exactament el bucle de l'apilat (A: b2_v108_flat2d; B: B2 V42 amb gir, correccions dels llargs, φ, LUT, màscara lunar,
flat ripple). Serveixen per a la prova global de l'autocalibratge A − B: si hi hagués un patró fix NOMÉS al sensor d'A (un fil o una pols
durant l'apuntament A), les dues estimacions independents E1 = A1 − B1 i E2 = A2 − B2 el mostrarien totes dues (correlació > nul).
Es desa la meitat de dalt del llenç (files 0–4200, on hi ha T1, T2 i el solapament gran), en G de sortida (espai de l'apilat), en G de
càmera (sense matriu) i el pes G. Ús: s8_meitats.py → 4-RESULTATS/v108_20260926/sony_A/meitats_flat2d/{A1,A2,B1,B2}.npz"""
import sys, json, time, math, os
from pathlib import Path
CRT = Path(__file__).resolve().parents[2] / 'v97_refundacio_20260924/cadena_raw'; sys.path.insert(0, str(CRT))
import a4_sources as _A4; _A4.CID = json.loads((_A4.R / '.coordination/claim.lock/owner.json').read_text())['claim_id']
assert _A4.CID == 'CLAUDE_V108_MARRONS_I_ZONES_NEGRES_20260926', _A4.CID
from a4_sources import *
guard(); t00 = time.time(); YMAX = 4200
OUT = _A4.R / '4-RESULTATS/v108_20260926/sony_A/meitats_flat2d'; OUT.mkdir(parents=True, exist_ok=True)
FL2D = Path(os.environ.get('FLAT2D_SONY') or _A4.R / '4-RESULTATS/v108_20260926/marrons/flat2d/SONYTOT_flat2d.npz')
_C = np.load(FL2D)['C'].astype(np.float32); _orig_init = f2.Ctx.__init__
def _init_flat2d(s, run):
    _orig_init(s, run); assert s.flat.shape == _C.shape; s.flat = (s.flat * _C).astype(np.float32)
f2.Ctx.__init__ = _init_flat2d
ns, fr = context(); ns.update(FLAT_CENTRE_YX={'sony': (2660., 4000.)}, FLAT_SIGMA_PX=32.)
definition(fr['sources']['common32']['copy'], 'flat_ripple_correction', ns); definition(H / 's4_v51_core_comu38.py', 'upsample', ns)
flat_ripple_correction = ns['flat_ripple_correction']; upsample = ns['upsample']; COMMON_TO_FINAL = ns['COMMON_TO_FINAL']
path = f12dirs['sony']; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run)
pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']
meta = json.loads((O / 'sources_v36/cau/sony_meta.json').read_text())['frames']
CORR_B = json.loads((H / 'b2_v42_correccions_B.json').read_text()); DELTA_B = math.radians(8.10 / 60.0)
fcorr, frep = flat_ripple_correction(ctx, 'sony'); inv = cv2.invertAffineTransform(COMMON_TO_FINAL); CHN = {0: 'R', 1: 'G', 2: 'B'}
Hh, Ww = YMAX, 10551; yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float32)
qx = inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]; qy = inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]; del xx, yy
dx0 = ((qx - ctx.CX) * ctx.k).astype(np.float32); dy0 = ((qy - ctx.CY) * ctx.k).astype(np.float32); del qx, qy
MEITATS = {'A1': ('sony_A', lambda t: t <= 18), 'A2': ('sony_A', lambda t: t >= 28), 'B1': ('sony_B', lambda t: t <= 70), 'B2': ('sony_B', lambda t: t >= 80)}
rep = dict(flat2d=str(FL2D), files_desades=[0, YMAX], matriu=np.asarray(run.matriu).tolist(), guany=np.asarray(run.color['guany']).tolist(), meitats={})
for mn, (grup, cond) in MEITATS.items():
    if (OUT / f'{mn}.npz').exists(): print('ja hi és', mn); continue
    names = [m['name'] for m in meta if m['group'] == grup]; phis = {c: np.load(O / 'sources_v36/cau' / f'{grup}_{c}_phi.npy', mmap_mode='r') for c in ('R', 'G', 'B')}
    num = np.zeros((Hh, Ww, 3), np.float32); den = np.zeros((Hh, Ww, 3), np.float32); usats = []
    if grup == 'sony_B':
        c_, s_ = math.cos(DELTA_B), math.sin(DELTA_B); dx, dy = (c_ * dx0 - s_ * dy0).astype(np.float32), (s_ * dx0 + c_ * dy0).astype(np.float32)
    else: dx, dy = dx0, dy0
    for j, n in enumerate(names):
        m = meta[[mm['name'] for mm in meta].index(n)]
        if not cond(m['t']): continue
        v = pos[n]; k = kq.get(n, 1.0); cx_, cy_ = CORR_B.get(n, (0.0, 0.0)) if grup == 'sony_B' else (0.0, 0.0)
        rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x'] + cx_).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y'] + cy_).astype(np.float32)
        vv = dict(v); vv['sol_x'] = v['sol_x'] + cx_; vv['sol_y'] = v['sol_y'] + cy_; fl = f2.mascara_lluna(ctx, vv, rx, ry)
        for i, (pl, w) in ctx.plans(n, v['exp']).items():
            c = comu.IDX_CANAL[i]; oy, ox = ctx.orig[i]
            if fcorr is not None: pl = pl * fcorr[i]
            mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
            dd = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
            nn = cv2.remap(pl * w * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
            b = float(m['offset_RGB'][c])
            if b != 0.0: nn += b * dd
            nn *= np.exp(-upsample(phis[CHN[c]][j])[:Hh]); num[..., c] += nn; den[..., c] += dd; del dd, nn, mx, my
        usats.append(dict(nom=n, exp=m['exp'], t=m['t'])); del rx, ry, fl
        print(f'{mn} {n} ({m["exp"]:g} s, t {m["t"]} s) · {time.time()-t00:.0f}s', flush=True)
    cam = np.where(den > 0, num / np.maximum(den, 1e-20), np.nan).astype(np.float32); del num
    _, u = comu.lluminancia(cam, run.matriu, run.color['guany'])
    np.savez(OUT / f'{mn}.npz', G=u[..., 1].astype(np.float32), Gcam=cam[..., 1], w=den[..., 1]); rep['meitats'][mn] = usats; del cam, u, den
save(OUT / 'REBUT.json', rep); print('FET', f'{time.time()-t00:.0f}s', flush=True)
