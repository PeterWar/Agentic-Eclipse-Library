"""s3 · FOTOGRAMA A FOTOGRAMA, a resolució plena, amb la calibració del pilot (flat 2D) o la de la cadena: per a cada fotograma de la Sony
(apuntament A: 9, apuntament B: 12) es refà exactament la seva aportació a l'apilat (mateix bucle que b2_v108_flat2d.py per a A i que el
programa congelat B2 V42 per a B: gir +8,10′, correccions per fotograma dels llargs, camps B1 φ, LUT, màscara lunar, flat ripple),
però SENSE sumar: es desa, dins de la caixa de cada traç, el G del fotograma (espai de color de l'apilat) i el seu pes (den G).
També es desen els paràmetres del mapatge llenç→sensor de cada fotograma, per passar qualsevol punt del llenç al sensor.
Ús: s3_fotogrames.py si|no   (flat 2D)   → 4-RESULTATS/v108_20260926/sony_A/fotogrames_<flat2d|control>/{T1,T2}_<nom>.npz + MAPATGE.json
Només lectura dels RAW i de la cadena; cap escriptura fora de 4-RESULTATS/v108_20260926/sony_A/."""
import sys, argparse, json, time, math, os
from pathlib import Path
CRT = Path(__file__).resolve().parents[2] / 'v97_refundacio_20260924/cadena_raw'; sys.path.insert(0, str(CRT))
import a4_sources as _A4; _A4.CID = json.loads((_A4.R / '.coordination/claim.lock/owner.json').read_text())['claim_id']
assert _A4.CID == 'CLAUDE_V108_MARRONS_I_ZONES_NEGRES_20260926', _A4.CID
from a4_sources import *   # context(), guard(), O, H, comu, f2, sha, save, definition, np, cv2
ap = argparse.ArgumentParser(); ap.add_argument('flat2d', choices=['si', 'no']); ap.add_argument('--marge-t2', type=int, default=400); ap.add_argument('--marge-t1', type=int, default=700)
a = ap.parse_args(); guard(); t00 = time.time()
OUT = _A4.R / '4-RESULTATS/v108_20260926/sony_A' / ('fotogrames_flat2d' if a.flat2d == 'si' else 'fotogrames_control'); OUT.mkdir(parents=True, exist_ok=True)
FL2D = Path(os.environ.get('FLAT2D_SONY') or _A4.R / '4-RESULTATS/v108_20260926/marrons/flat2d/SONYTOT_flat2d.npz')
if a.flat2d == 'si':
    _C = np.load(FL2D)['C'].astype(np.float32); _orig_init = f2.Ctx.__init__
    def _init_flat2d(s, run):
        _orig_init(s, run); assert s.flat.shape == _C.shape, (s.flat.shape, _C.shape); s.flat = (s.flat * _C).astype(np.float32)
    f2.Ctx.__init__ = _init_flat2d
g = json.loads((_A4.R / '4-RESULTATS/v108_20260926/marrons/M3_GEOMETRIA.json').read_text())
Hh, Ww = 7506, 10551
def caixa(k, marge):
    e = np.array(g[str(k)]['extrems']); return (int(max(0, e[:, 0].min() - marge)), int(max(0, e[:, 1].min() - marge)), int(min(Ww, e[:, 0].max() + marge)), int(min(Hh, e[:, 1].max() + marge)))
CAIXES = {'T1': caixa(1, a.marge_t1), 'T2': caixa(2, a.marge_t2)}
ns, fr = context(); ns.update(FLAT_CENTRE_YX={'sony': (2660., 4000.)}, FLAT_SIGMA_PX=32.)
definition(fr['sources']['common32']['copy'], 'flat_ripple_correction', ns); definition(H / 's4_v51_core_comu38.py', 'upsample', ns)
flat_ripple_correction = ns['flat_ripple_correction']; upsample = ns['upsample']; COMMON_TO_FINAL = ns['COMMON_TO_FINAL']
path = f12dirs['sony']; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run)
pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']
meta = json.loads((O / 'sources_v36/cau/sony_meta.json').read_text())['frames']
CORR_B = json.loads((H / 'b2_v42_correccions_B.json').read_text()); DELTA_B = math.radians(8.10 / 60.0)
fcorr, frep = flat_ripple_correction(ctx, 'sony')
inv = cv2.invertAffineTransform(COMMON_TO_FINAL)
CHN = {0: 'R', 1: 'G', 2: 'B'}
mapatge = dict(nota='llenç (x,y) → q = inv(COMMON_TO_FINAL)·(x,y,1); d = (q − (CX,CY))·k; per a B, d girat δ; sensor rx = ca·dx + sa·dy + sol_x + cx, ry = −sa·dx + ca·dy + sol_y + cy (píxels RAW)',
               inv_common_to_final=inv, CX=float(ctx.CX), CY=float(ctx.CY), k=float(ctx.k), ca=float(ctx.ca), sa=float(ctx.sa), RL=float(ctx.RL), delta_B_rad=DELTA_B, flat2d=a.flat2d, fitxer_flat2d=str(FL2D) if a.flat2d == 'si' else None,
               caixes=CAIXES, fotogrames={})
for grup in ('sony_A', 'sony_B'):
    names = [m['name'] for m in meta if m['group'] == grup]
    phis = {c: np.load(O / 'sources_v36/cau' / f'{grup}_{c}_phi.npy', mmap_mode='r') for c in ('R', 'G', 'B')}
    for j, n in enumerate(names):
        v = pos[n]; k = kq.get(n, 1.0); m = meta[[mm['name'] for mm in meta].index(n)]
        cx_, cy_ = CORR_B.get(n, (0.0, 0.0)) if grup == 'sony_B' else (0.0, 0.0)
        mapatge['fotogrames'][n] = dict(grup=grup, j=j, exp=v['exp'], t=m.get('t'), sol_x=float(v['sol_x']), sol_y=float(v['sol_y']), cx=float(cx_), cy=float(cy_), k_coherencia=float(k), offset_RGB=m['offset_RGB'])
        plans = None; PHI = {}
        for tn, (x0, y0, x1, y1) in CAIXES.items():
            yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            qx = inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]; qy = inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]
            dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
            if grup == 'sony_B':
                c_, s_ = math.cos(DELTA_B), math.sin(DELTA_B); dx, dy = (c_ * dx - s_ * dy), (s_ * dx + c_ * dy)
            rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x'] + cx_).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y'] + cy_).astype(np.float32)
            vv = dict(v); vv['sol_x'] = v['sol_x'] + cx_; vv['sol_y'] = v['sol_y'] + cy_; fl = f2.mascara_lluna(ctx, vv, rx, ry)
            if plans is None: plans = ctx.plans(n, v['exp'])
            num = np.zeros((y1 - y0, x1 - x0, 3), np.float32); den = np.zeros_like(num)
            for i, (pl, w) in plans.items():
                c = comu.IDX_CANAL[i]; oy, ox = ctx.orig[i]
                if fcorr is not None: pl = pl * fcorr[i]
                mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
                dd = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
                nn = cv2.remap(pl * w * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
                b = float(m['offset_RGB'][c])
                if b != 0.0: nn += b * dd
                if c not in PHI: PHI[c] = upsample(phis[CHN[c]][j])
                phi = PHI[c][y0:y1, x0:x1]; nn *= np.exp(-phi)
                num[..., c] += nn; den[..., c] += dd; del dd, nn, phi
            cam = np.where(den > 0, num / np.maximum(den, 1e-20), np.nan)
            _, u = comu.lluminancia(cam, run.matriu, run.color['guany'])
            np.savez(OUT / f'{tn}_{n[:-4]}.npz', G=u[..., 1].astype(np.float32), w=den[..., 1].astype(np.float32))
            del num, den, cam, u, rx, ry, fl, qx, qy, dx, dy, xx, yy
        print(f'{grup} {n} ({v["exp"]:g} s, t {m.get("t")} s) fet · {time.time()-t00:.0f}s', flush=True); del plans, PHI
save(OUT / 'MAPATGE.json', mapatge); print('FET', f'{time.time()-t00:.0f}s', flush=True)
