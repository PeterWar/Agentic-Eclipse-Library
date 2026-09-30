"""s6 · EN QUIN FOTOSITS ÉS EL TRAÇ? Apilats per SUBPLÀ de Bayer (R, G1, G2, B), en espai de CÀMERA (abans de la matriu de color), a les
caixes de T1 i T2, per a cada apuntament i per a meitats temporals. Mateix bucle i mateixa calibració que s3 (A: b2_v108_flat2d; B: B2 V42
amb gir, correccions dels llargs, φ, LUT, màscara lunar, flat ripple), però el G1 i el G2 no es barregen i no s'aplica la matriu.
  · Un defecte de TRANSMISSIÓ (fil, pols, flat) o un buit REAL del cel és a tots quatre subplans (en relatiu, gairebé igual als quatre si
    és acromàtic; si és corona sobre cel blau, R ≥ G ≥ B però mai de signe contrari).
  · Un defecte de LECTURA del sensor (fotosits d'enfocament PDAF, files, un sol verd) és a un subplà i no als altres.
Ús: s6_subplans.py si|no → 4-RESULTATS/v108_20260926/sony_A/subplans_<flat2d|control>/{T1,T2}_<grup>.npz (num_i, den_i, i = 0 R, 1 G1, 2 B, 3 G2)"""
import sys, argparse, json, time, math, os
from pathlib import Path
CRT = Path(__file__).resolve().parents[2] / 'v97_refundacio_20260924/cadena_raw'; sys.path.insert(0, str(CRT))
import a4_sources as _A4; _A4.CID = json.loads((_A4.R / '.coordination/claim.lock/owner.json').read_text())['claim_id']
assert _A4.CID == 'CLAUDE_V108_MARRONS_I_ZONES_NEGRES_20260926', _A4.CID
from a4_sources import *
ap = argparse.ArgumentParser(); ap.add_argument('flat2d', choices=['si', 'no']); ap.add_argument('--marge-t2', type=int, default=300); ap.add_argument('--marge-t1', type=int, default=700)
a = ap.parse_args(); guard(); t00 = time.time()
OUT = _A4.R / '4-RESULTATS/v108_20260926/sony_A' / ('subplans_flat2d' if a.flat2d == 'si' else 'subplans_control'); OUT.mkdir(parents=True, exist_ok=True)
FL2D = Path(os.environ.get('FLAT2D_SONY') or _A4.R / '4-RESULTATS/v108_20260926/marrons/flat2d/SONYTOT_flat2d.npz')
if a.flat2d == 'si':
    _C = np.load(FL2D)['C'].astype(np.float32); _orig_init = f2.Ctx.__init__
    def _init_flat2d(s, run):
        _orig_init(s, run); assert s.flat.shape == _C.shape; s.flat = (s.flat * _C).astype(np.float32)
    f2.Ctx.__init__ = _init_flat2d
g = json.loads((_A4.R / '4-RESULTATS/v108_20260926/marrons/M3_GEOMETRIA.json').read_text()); Hh, Ww = 7506, 10551
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
fcorr, frep = flat_ripple_correction(ctx, 'sony'); inv = cv2.invertAffineTransform(COMMON_TO_FINAL); CHN = {0: 'R', 1: 'G', 2: 'B'}
GRUPS = {'A': lambda m: m['group'] == 'sony_A', 'B': lambda m: m['group'] == 'sony_B'}
if a.flat2d == 'si':
    GRUPS.update({'A_primers': lambda m: m['group'] == 'sony_A' and m['t'] <= 18, 'A_darrers': lambda m: m['group'] == 'sony_A' and m['t'] >= 28,
                  'B_primers': lambda m: m['group'] == 'sony_B' and m['t'] <= 70, 'B_darrers': lambda m: m['group'] == 'sony_B' and m['t'] >= 80})
ACC = {(gn, tn): (np.zeros((4, y1 - y0, x1 - x0), np.float32), np.zeros((4, y1 - y0, x1 - x0), np.float32)) for gn in GRUPS for tn, (x0, y0, x1, y1) in CAIXES.items()}
for grup in ('sony_A', 'sony_B'):
    names = [m['name'] for m in meta if m['group'] == grup]
    phis = {c: np.load(O / 'sources_v36/cau' / f'{grup}_{c}_phi.npy', mmap_mode='r') for c in ('R', 'G', 'B')}
    for j, n in enumerate(names):
        v = pos[n]; k = kq.get(n, 1.0); m = meta[[mm['name'] for mm in meta].index(n)]; cx_, cy_ = CORR_B.get(n, (0.0, 0.0)) if grup == 'sony_B' else (0.0, 0.0)
        gs = [gn for gn, f in GRUPS.items() if f(m)]; plans = ctx.plans(n, v['exp']); PHI = {}
        for tn, (x0, y0, x1, y1) in CAIXES.items():
            yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            qx = inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]; qy = inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]; dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
            if grup == 'sony_B':
                c_, s_ = math.cos(DELTA_B), math.sin(DELTA_B); dx, dy = (c_ * dx - s_ * dy), (s_ * dx + c_ * dy)
            rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x'] + cx_).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y'] + cy_).astype(np.float32)
            vv = dict(v); vv['sol_x'] = v['sol_x'] + cx_; vv['sol_y'] = v['sol_y'] + cy_; fl = f2.mascara_lluna(ctx, vv, rx, ry)
            for i, (pl, w) in plans.items():
                c = comu.IDX_CANAL[i]; oy, ox = ctx.orig[i]
                if fcorr is not None: pl = pl * fcorr[i]
                mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
                dd = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
                nn = cv2.remap(pl * w * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
                b = float(m['offset_RGB'][c])
                if b != 0.0: nn += b * dd
                if c not in PHI: PHI[c] = upsample(phis[CHN[c]][j])
                nn *= np.exp(-PHI[c][y0:y1, x0:x1])
                for gn in gs:
                    ACC[(gn, tn)][0][i] += nn; ACC[(gn, tn)][1][i] += dd
                del dd, nn
            del rx, ry, fl, qx, qy, dx, dy, xx, yy
        print(f'{grup} {n} ({v["exp"]:g} s) → {gs} · {time.time()-t00:.0f}s', flush=True); del plans, PHI
for (gn, tn), (nu, de) in ACC.items():
    np.savez(OUT / f'{tn}_{gn}.npz', num=nu, den=de)
save(OUT / 'REBUT.json', dict(flat2d=a.flat2d, caixes=CAIXES, grups=list(GRUPS), index_subpla={'0': 'R', '1': 'G1', '2': 'B', '3': 'G2'}, orig=ctx.orig, segons=time.time() - t00))
print('FET', f'{time.time()-t00:.0f}s', flush=True)
