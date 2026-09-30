"""a9b_flat2d_v2 (V108, flat 2D lliurable) · Els 67 fotogrames Vixen de la CAIXA LUNAR (limb_frames: numeradors i pesos per canal a la graella
final i distància al limbe modelat) amb el MATEIX flat 2D que els apilats (f0_flat2d_v2.py): cada subpla es divideix, a més, per C.
Sense això, la franja arran del limbe (a3d) i la resta del llenç es calibrarien amb flats diferents i quedaria una costura quadrada a la vora de
la caixa (1.400 × 1.400 px). Còpia literal de v98_20260925/a9b_limb_frames_comuna.py (finestra comuna, la de la V98–V107); l'únic canvi és
`s.flat = FLAT_RADIAL · C` quan f2.Ctx carrega el flat (i el claim). La Vixen no té correcció d'ondulació (FLAT_CENTRE_YX només té la Sony).
Control: amb --flat2d no ha de reproduir 4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna bit a bit (numerator, weight, distance_model).
Ús: a9b_flat2d_v2.py --flat2d si|no --out <carpeta>"""
import sys, argparse, os
from pathlib import Path
T97 = Path(__file__).resolve().parents[2] / 'v97_refundacio_20260924/cadena_raw'; sys.path.insert(0, str(T97))
import a4_sources as A4
A4.CID = 'CLAUDE_V108_MARRONS_I_ZONES_NEGRES_20260926'
from a4_sources import *
ap = argparse.ArgumentParser(); ap.add_argument('--flat2d', choices=['si', 'no'], required=True); ap.add_argument('--out', required=True); a = ap.parse_args()
A4.guard()
FL2D = Path(os.environ.get('FLAT2D_VIXEN') or A4.R / '4-RESULTATS/v108_20260926/flat2d_v2/flat2d/VIXEN_flat2d_v2.npz'); INJ = {}
_orig_init = f2.Ctx.__init__
_C = np.load(FL2D)['C'].astype(np.float32) if a.flat2d == 'si' else None
def _init_v2(s, run):
    _orig_init(s, run); s.flat_original = s.flat
    if _C is not None:
        assert s.flat.shape == _C.shape, (s.flat.shape, _C.shape); s.flat = (s.flat * _C).astype(np.float32); INJ['fet'] = True
f2.Ctx.__init__ = _init_v2
ns, fr = context()
def plans_comuna(s, nom, e):
    """Còpia literal de b2_v97.py (V97)."""
    import rawpy
    with rawpy.imread(s.ruta[nom]) as r: raw = r.raw_image.astype(np.float32)
    dk = s.dark(e); ped = s.cfg['pedestal_dn']; sat = s.cfg['saturacio_dn']; es_sony = s.run.tren.upper().startswith('SONY')
    fs = [raw[s.orig[i][0]::2, s.orig[i][1]::2] - ped for i in range(4)]
    hh = min(x.shape[0] for x in fs); ww = min(x.shape[1] for x in fs); fs = [x[:hh, :ww] for x in fs]
    fmax = np.maximum.reduce(fs)
    gi = [i for i in range(4) if comu.IDX_CANAL[i] == 1]; fg = sum(fs[i] for i in gi) / len(gi)
    alt = f2.SOSTRE * (sat - ped)
    sostre = 1.0 - ns['smooth'](fmax, ns['RAMPA_INICI'] * alt, alt)
    terra = np.clip((fg - f2.TERRA_DN) / (3.0 * f2.TERRA_DN), 0.0, 1.0)
    wcom = (sostre * terra * e).astype(np.float32)
    out = {}
    for i in range(4):
        oy, ox = s.orig[i]; rs = raw[oy::2, ox::2]; ds = dk[oy::2, ox::2]
        if es_sony: rs = ds + (rs - ds) * ns['lin_corr_sony'](rs, ped, sat)
        pl = comu.calibra_pla(rs, ds, s.flat[oy::2, ox::2], e, s.wb, s.mc, i)
        v = s.valid[oy::2, ox::2]; w = np.zeros(pl.shape, np.float32); w[:hh, :ww] = wcom * v[:hh, :ww]
        out[i] = (pl, w)
    return out
f2.Ctx.plans = plans_comuna
O2 = Path(a.out); O2.mkdir(parents=True, exist_ok=True)
# ---- bucle de a9_limb_frames.collect (literal), amb la sortida a O2
ns.update(FLAT_CENTRE_YX={'sony': (2660., 4000.)}, FLAT_SIGMA_PX=32.)
definition(fr['sources']['common32']['copy'], 'flat_ripple_correction', ns); definition(H / 's4_v51_core_comu38.py', 'upsample', ns)
path = f12dirs['vixen']; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run); pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']; meta = json.loads((O / 'sources_v36/cau/vixen_meta.json').read_text())['frames']; names = [m['name'] for m in meta]
hold = json.loads((O / 'QA_FROZEN.json').read_text())['development_validation']['new_holdout']
box = [3077, 4477, 4677, 6077]; y0, y1, x0, x1 = box; h, w = y1 - y0, x1 - x0; nF = len(names)
shape = (nF, h, w, 3); N = np.lib.format.open_memmap(O2 / 'numerator.npy', mode='w+', dtype='float32', shape=shape); Wg = np.lib.format.open_memmap(O2 / 'weight.npy', mode='w+', dtype='float32', shape=shape); Ds = np.lib.format.open_memmap(O2 / 'distance_model.npy', mode='w+', dtype='float32', shape=(nF, h, w))
phis = {c: np.load(O / 'sources_v36/cau' / f'vixen_{c}_phi.npy', mmap_mode='r') for c in ['R', 'G', 'B']}
_sv = ctx.flat; ctx.flat = ctx.flat_original; fcorr, _ = ns['flat_ripple_correction'](ctx, 'vixen'); ctx.flat = _sv   # None per a la Vixen
inv = cv2.invertAffineTransform(ns['COMMON_TO_FINAL']); yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); qx = inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]; qy = inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]; dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
info = []; t0 = time.monotonic()
for j, n in enumerate(names):
    v = pos[n]; k = kq.get(n, 1.); m = meta[j]; rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x']).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y']).astype(np.float32); mlx = v['sol_x'] + float(v['lluna_dx']); mly = v['sol_y'] + float(v['lluna_dy']); Ds[j] = (np.hypot(rx - mlx, ry - mly) - ctx.RL).astype(np.float32)
    N[j] = 0; Wg[j] = 0; plans = ctx.plans(n, v['exp']); pmap = {c: ns['upsample'](phis[c][j])[y0:y1, x0:x1] for c in phis}
    for i, (pl, wgt) in plans.items():
        c = comu.IDX_CANAL[i]; oy, ox = ctx.orig[i]
        if fcorr is not None: pl = pl * fcorr[i]
        mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32); dd = cv2.remap(wgt, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); nn = cv2.remap(pl * wgt * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); b = float(m['offset_RGB'][c])
        if b != 0: nn = nn + b * dd
        nn = nn * np.exp(-pmap[{0: 'R', 1: 'G', 2: 'B'}[c]]); N[j, ..., c] += nn; Wg[j, ..., c] += dd
    info.append({'name': n, 'time': m['t'], 'exposure': v['exp'], 'holdout': n in hold, 'lluna_dx': v['lluna_dx'], 'lluna_dy': v['lluna_dy'], 'k': k})
    del plans, pmap, rx, ry
    if j % 10 == 0 or j == nF - 1: print('LIMB_FRAME', j + 1, nF, round(time.monotonic() - t0, 1), flush=True)
for arr in [N, Wg, Ds]: arr.flush()
save(O2 / 'METADATA.json', {'box_y0y1x0x1': box, 'shape': list(shape), 'frames': info, 'matrix': run.matriu, 'gain': run.color['guany'], 'radius_model': ctx.RL, 'common_to_final': ns['COMMON_TO_FINAL'], 'finestra': 'comuna', 'distances': 'relative to modelled radius', 'stage': 'per-frame native balanced CFA RGB, after frozen offsets/phi (V98: finestra comuna; V108: flat 2D ' + a.flat2d + ')', 'flat2d': a.flat2d, 'fitxer_flat2d': str(FL2D) if a.flat2d == 'si' else None, 'injectat': INJ})
rows = [{'name': name, 'sha256': sha(O2 / name)} for name in ['numerator.npy', 'weight.npy', 'distance_model.npy']]
ref = json.loads((A4.R / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna/COMPLETE.json').read_text())['files']; refd = {r_['name']: r_['sha256'] for r_ in ref}
for r_ in rows: r_['igual_a_la_cadena'] = (r_['sha256'] == refd.get(r_['name']))
save(O2 / 'COMPLETE.json', {'PASS': True, 'files': rows, 'seconds': time.monotonic() - t0, 'flat2d': a.flat2d}); print('LIMB_COMPLETE', [(r_['name'], r_['igual_a_la_cadena']) for r_ in rows], flush=True)
