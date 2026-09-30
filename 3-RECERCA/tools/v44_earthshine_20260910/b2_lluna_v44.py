"""V44 derivative of V43 B2: one normalized raw-CFA interpolation; fine shift folded in mapping. Existing calibration, geometry, color and field retained. No drizzle or output resizing."""
from comu44 import *
import importlib.util as _iu, math
_sp = _iu.spec_from_file_location('b2v38', HERE38 / 'b2_recomposicio.py'); B = _iu.module_from_spec(_sp); _sp.loader.exec_module(B)
MC = (CX + 14.8, CY + 0.9); WIN = 700; MARGE_PX = 40.0; VORA_PX = 3.0


def main():
    prepare(); tag, nom = sys.argv[1], sys.argv[2]; args = dict(a.split('=', 1) for a in sys.argv[3:] if '=' in a)
    path = RUNS[tag]; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run); pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']
    meta = json.loads((CAU36 / f'{tag}_meta.json').read_text())['frames']; m = meta[[mm['name'] for mm in meta].index(nom)]; group = tag if tag == 'vixen' else m['group']
    names = [mm['name'] for mm in meta if (tag == 'vixen' or mm['group'] == group)]; j = names.index(nom)
    phis = {c: np.load(CAU36 / f'{group}_{c}_phi.npy', mmap_mode='r') for c in ('R', 'G', 'B')}; fcorr, frep = B.flat_ripple_correction(ctx, tag)
    delta = math.radians(float(args.get('delta_arcmin', 0.0)) / 60.0) if group == 'sony_B' else 0.0; corr = json.loads(Path(args['corr']).read_text()) if ('corr' in args and group == 'sony_B') else {}; cx_, cy_ = corr.get(nom, (0.0, 0.0))
    inv = cv2.invertAffineTransform(COMMON_TO_FINAL); x0, y0 = int(round(MC[0])) - WIN, int(round(MC[1])) - WIN; yy, xx = np.mgrid[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN].astype(np.float32)
    sx, sy = float(args.get('sx', 0)), float(args.get('sy', 0))
    xx -= sx; yy -= sy  # combine final lunar correction BEFORE the only CFA remap
    qx = inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]; qy = inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]; dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
    if delta != 0.0: c_, s_ = math.cos(delta), math.sin(delta); dx, dy = (c_ * dx - s_ * dy), (s_ * dx + c_ * dy)
    v = pos[nom]; k = kq.get(nom, 1.0)
    # desplaçament perquè la Lluna del fotograma caigui a M_c: la posició de M_c al comú → offset respecte del Sol
    qmx = inv[0, 0] * MC[0] + inv[0, 1] * MC[1] + inv[0, 2]; qmy = inv[1, 0] * MC[0] + inv[1, 1] * MC[1] + inv[1, 2]; dmx, dmy = (qmx - ctx.CX) * ctx.k, (qmy - ctx.CY) * ctx.k
    if delta != 0.0: dmx, dmy = (c_ * dmx - s_ * dmy), (s_ * dmx + c_ * dmy)
    off_x = float(v['lluna_dx']) - (ctx.ca * dmx + ctx.sa * dmy); off_y = float(v['lluna_dy']) - (-ctx.sa * dmx + ctx.ca * dmy)   # sol' = sol + lluna − Rm·d(M_c)
    rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x'] + cx_ + off_x).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y'] + cy_ + off_y).astype(np.float32)
    mlx = v['sol_x'] + cx_ + float(v['lluna_dx']); mly = v['sol_y'] + cy_ + float(v['lluna_dy']); dl = np.hypot(rx - mlx, ry - mly)
    disc = np.clip(((ctx.RL + MARGE_PX * ctx.k) - dl) / (VORA_PX * ctx.k), 0, 1).astype(np.float32)   # DINS del limbe + marge
    num = np.zeros((2 * WIN, 2 * WIN, 3), np.float32); den = np.zeros_like(num); plans = ctx.plans(nom, v['exp'])
    for i, (pl, w) in plans.items():
        c = comu.IDX_CANAL[i]; oy, ox = ctx.orig[i]
        if fcorr is not None: pl = pl * fcorr[i]
        mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
        dd = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * disc; nn = cv2.remap(pl * w * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * disc
        b = float(m['offset_RGB'][c])
        if b != 0.0: nn += b * dd
        phi_full = B.upsample(phis[B.CHN[c]][j]); phi = cv2.remap(phi_full, xx, yy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE); nn *= np.exp(-phi); num[..., c] += nn; den[..., c] += dd
    cam = np.where(den > 0, num / np.maximum(den, 1e-20), np.nan); _, total = comu.lluminancia(cam, run.matriu, run.color['guany']); total = total.astype(np.float32)
    stem = nom.split('.')[0]; np.save(CAU44 / f'lluna_{tag}_{stem}_v44.npy', total); np.save(CAU44 / f'lluna_{tag}_{stem}_v44_pes.npy', den[..., 1].astype(np.float32))
    ok = np.isfinite(total[..., 1]); r_c = np.hypot(xx - MC[0], yy - MC[1]); inner = ok & (r_c < 0.85 * 453.5)
    rep = dict(single_CFA_remap=True, correccio_lunar_final_px=[sx,sy], fotograma=nom, tren=tag, grup=group, exp=v['exp'], t=v.get('t'), delta_arcmin=math.degrees(delta) * 60, correccio_sol_px=[cx_, cy_], finestra=[x0, y0, 2 * WIN, 2 * WIN], centre_lluna_llenc=list(MC), RL_sensor=float(ctx.RL), k=float(ctx.k), px_valids=int(ok.sum()), mediana_G_interior=float(np.nanmedian(total[..., 1][inner])) if inner.any() else None, frac_saturada_interior=float(1 - (den[..., 1][inner] > 0).mean()) if inner.any() else None)
    savejson(REB44 / f'B2L_{tag}_{stem}.json', rep); log(f"{nom} ({v['exp']:g} s, t {v.get('t')}): {rep['px_valids']} px vàlids · mediana G interior {rep['mediana_G_interior']} · sense dada a l'interior {100 * (rep['frac_saturada_interior'] or 0):.1f} %")


if __name__ == '__main__':
    main()
