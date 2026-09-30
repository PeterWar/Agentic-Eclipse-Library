"""a9b (V98) · Els fotogrames de la caixa lunar (limb_frames: 67 fotogrames Vixen, numeradors i pesos per canal a la graella final, i distància
al limbe modelat de cada fotograma) refets amb la FINESTRA COMUNA de la V97 (un sol pes per cel·la Bayer: sostre pel subpla més exposat, terra pel G).
Per què: la V97 va passar la Vixen a la finestra comuna (el polígon B/G i els pentàgons de la 49), però els limb_frames eren els de la V85
(finestra per canal) i la franja d'un instant se'n feia. Codi: el de a9_limb_frames.py de cadena_raw (còpia literal del bucle) amb
f2.Ctx.plans = plans_comuna (còpia literal de b2_v97.py). Només canvia la finestra; la calibració, el registre, k, φ i la geometria són els congelats.
Control: amb --finestra canal ha de reproduir els limb_frames de cadena_raw bit a bit (numerator.npy, weight.npy, distance_model.npy).
Ús: a9b_limb_frames_comuna.py --finestra comuna|canal --out <carpeta>"""
import sys, argparse
from pathlib import Path
T97 = Path('/Users/USUARI/Desktop/Eclipse 2026/3-RECERCA/tools/v97_refundacio_20260924/cadena_raw'); sys.path.insert(0, str(T97))
import a4_sources as A4
A4.CID = 'CODEX_V105_LIMBE_OBSERVAT_20260926'
from a4_sources import *
ap = argparse.ArgumentParser(); ap.add_argument('--finestra', choices=['canal', 'comuna'], required=True); ap.add_argument('--out', required=True); ap.add_argument('--floor', type=float, choices=[0.,12.], required=True); ap.add_argument('--indices', default='0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,34'); a = ap.parse_args()
A4.guard()
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
    terra = np.ones_like(fg) if a.floor == 0 else np.clip((fg - f2.TERRA_DN) / (3.0 * f2.TERRA_DN), 0.0, 1.0)
    wcom = (sostre * terra * e).astype(np.float32)
    out = {}
    for i in range(4):
        oy, ox = s.orig[i]; rs = raw[oy::2, ox::2]; ds = dk[oy::2, ox::2]
        if es_sony: rs = ds + (rs - ds) * ns['lin_corr_sony'](rs, ped, sat)
        pl = comu.calibra_pla(rs, ds, s.flat[oy::2, ox::2], e, s.wb, s.mc, i)
        v = s.valid[oy::2, ox::2]; w = np.zeros(pl.shape, np.float32); w[:hh, :ww] = wcom * v[:hh, :ww]
        out[i] = (pl, w)
    return out
if a.finestra == 'comuna': f2.Ctx.plans = plans_comuna
O2 = Path(a.out); assert str(O2).startswith('/private/tmp/v105_raw_pilot_20260926/'); assert not O2.exists(); O2.mkdir(parents=True)
# ---- bucle de a9_limb_frames.collect (literal), amb la sortida a O2
ns.update(FLAT_CENTRE_YX={'sony': (2660., 4000.)}, FLAT_SIGMA_PX=32.)
definition(fr['sources']['common32']['copy'], 'flat_ripple_correction', ns); definition(H / 's4_v51_core_comu38.py', 'upsample', ns)
path = f12dirs['vixen']; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run); pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']; meta = json.loads((O / 'sources_v36/cau/vixen_meta.json').read_text())['frames']; selected = [(i,meta[i]['name']) for i in map(int,a.indices.split(','))]; names = [n for _,n in selected]
hold = json.loads((O / 'QA_FROZEN.json').read_text())['development_validation']['new_holdout']
box = [3077, 4477, 4677, 6077]; y0, y1, x0, x1 = box; h, w = y1 - y0, x1 - x0; nF = len(names)
shape = (nF, h, w, 3); N = np.lib.format.open_memmap(O2 / 'numerator.npy', mode='w+', dtype='float32', shape=shape); Wg = np.lib.format.open_memmap(O2 / 'weight.npy', mode='w+', dtype='float32', shape=shape); Ds = np.lib.format.open_memmap(O2 / 'distance_model.npy', mode='w+', dtype='float32', shape=(nF, h, w))
phis = {c: np.load(O / 'sources_v36/cau' / f'vixen_{c}_phi.npy', mmap_mode='r') for c in ['R', 'G', 'B']}; fcorr, _ = ns['flat_ripple_correction'](ctx, 'vixen')
inv = cv2.invertAffineTransform(ns['COMMON_TO_FINAL']); yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); qx = inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]; qy = inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]; dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
info = []; t0 = time.monotonic()
for jj, (j, n) in enumerate(selected):
    v = pos[n]; k = kq.get(n, 1.); m = meta[j]; rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x']).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y']).astype(np.float32); mlx = v['sol_x'] + float(v['lluna_dx']); mly = v['sol_y'] + float(v['lluna_dy']); Ds[jj] = (np.hypot(rx - mlx, ry - mly) - ctx.RL).astype(np.float32)
    N[jj] = 0; Wg[jj] = 0; plans = ctx.plans(n, v['exp']); pmap = {c: ns['upsample'](phis[c][j])[y0:y1, x0:x1] for c in phis}
    for i, (pl, wgt) in plans.items():
        c = comu.IDX_CANAL[i]; oy, ox = ctx.orig[i]
        if fcorr is not None: pl = pl * fcorr[i]
        mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32); dd = cv2.remap(wgt, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); nn = cv2.remap(pl * wgt * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); b = float(m['offset_RGB'][c])
        if b != 0: nn = nn + b * dd
        nn = nn * np.exp(-pmap[{0: 'R', 1: 'G', 2: 'B'}[c]]); N[jj, ..., c] += nn; Wg[jj, ..., c] += dd
    info.append({'original_index': j, 'name': n, 'time': m['t'], 'exposure': v['exp'], 'holdout': n in hold, 'lluna_dx': v['lluna_dx'], 'lluna_dy': v['lluna_dy'], 'k': k})
    del plans, pmap, rx, ry
    if True: print('LIMB_FRAME', jj + 1, nF, round(time.monotonic() - t0, 1), flush=True)
for arr in [N, Wg, Ds]: arr.flush()
save(O2 / 'METADATA.json', {'box_y0y1x0x1': box, 'shape': list(shape), 'frames': info, 'matrix': run.matriu, 'gain': run.color['guany'], 'radius_model': ctx.RL, 'common_to_final': ns['COMMON_TO_FINAL'], 'finestra': a.finestra, 'floor_dn': a.floor, 'producer_original_sha256': 'e51d7bfa78bd48ba6eb8498ecc2c5a8dec70b99828da467043367c28ec9e8686', 'distances': 'relative to modelled radius', 'stage': 'per-frame native balanced CFA RGB, after frozen offsets/phi (V98: finestra ' + a.finestra + ')'})
rows = [{'name': name, 'sha256': sha(O2 / name)} for name in ['numerator.npy', 'weight.npy', 'distance_model.npy']]; save(O2 / 'COMPLETE.json', {'PASS': True, 'files': rows, 'seconds': time.monotonic() - t0}); print('LIMB_COMPLETE', flush=True)
