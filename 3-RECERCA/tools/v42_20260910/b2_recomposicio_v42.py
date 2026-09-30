"""B2 (V42) · Recomposició de l'apuntament B de la Sony (i, si cal, de qualsevol grup) amb DUES correccions mesurades a les estrelles (research/159):
 (1) ROTACIÓ de camp de l'apuntament B al voltant del Sol (δ, en minuts d'arc; mesurada +8,10′ a 11 estrelles amb nul; la cadena només aplicava una rotació per run);
 (2) correccions de TRANSLACIÓ per fotograma per als fotogrames llargs de B (DSC06993 8 s, DSC06996 i DSC06999 2 s), que el registre F1.3 posava per «model» i deixaven
     una traça de 3,7–4,7 px (research/125): es mesuren a les estrelles contra l'apuntament A (e2) i s'apliquen com a desplaçament de (sol_x, sol_y) del fotograma.
Tota la resta és la B2 de la V38 (mateixos pesos, camps B1, flat, LUT Sony, màscara lunar per fotograma). Sortida: cau/{grup}_total_v42{sufix}.npy (+ pesos G).
Ús: b2_recomposicio_v42.py sony_B [delta_arcmin=8.10] [nomes=DSC06993,DSC06996] [corr=cau/correccions_B.json] [sufix=_prova]"""
from comu42 import *
import importlib.util as _iu, time, math
_sp = _iu.spec_from_file_location('b2v38', HERE38 / 'b2_recomposicio.py'); B = _iu.module_from_spec(_sp); _sp.loader.exec_module(B)   # TAULA, classe, correccio_vora, flat_ripple_correction, upsample, CHN
GROUPS = {'vixen': ('vixen', None), 'sony_A': ('sony', 'sony_A'), 'sony_B': ('sony', 'sony_B')}


def main():
    args = dict(a.split('=', 1) for a in sys.argv[2:] if '=' in a); group = sys.argv[1]; tag, grp = GROUPS[group]
    delta = math.radians(float(args.get('delta_arcmin', 0.0)) / 60.0); nomes = set(args['nomes'].split(',')) if 'nomes' in args else None; sufix = args.get('sufix', '')
    corr = json.loads(Path(args['corr']).read_text()) if 'corr' in args else {}   # {nom: [dsol_x, dsol_y]} en píxels del SENSOR
    inv = cv2.invertAffineTransform(COMMON_TO_FINAL); yy, xx = np.ogrid[:H, :W]
    qx = (inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]).astype(np.float32); qy = (inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]).astype(np.float32)
    path = RUNS[tag]; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run)
    pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']
    meta = json.loads((CAU36 / f'{tag}_meta.json').read_text())['frames']; names = [m['name'] for m in meta if (grp is None or m['group'] == grp)]
    b1 = json.loads((REB36 / f'B1_camps_{group}.json').read_text()); assert b1['frames'] == names
    phis = {c: np.load(CAU36 / f'{group}_{c}_phi.npy', mmap_mode='r') for c in ('R', 'G', 'B')}
    fcorr, frep = B.flat_ripple_correction(ctx, tag)
    num = np.zeros((H, W, 3), np.float32); den = np.zeros((H, W, 3), np.float32)
    dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
    if delta != 0.0:   # rotació de l'apuntament al voltant del Sol (el centre de (dx, dy))
        c_, s_ = math.cos(delta), math.sin(delta); dx, dy = (c_ * dx - s_ * dy).astype(np.float32), (s_ * dx + c_ * dy).astype(np.float32)
    log(f'{group}: δ = {math.degrees(delta) * 60:+.2f}′ · correccions per fotograma: {corr or "cap"} · fotogrames: {"tots" if nomes is None else sorted(nomes)}')
    t0 = time.time(); applied = []
    for j, n in enumerate(names):
        if nomes is not None and n not in nomes: continue
        v = pos[n]; k = kq.get(n, 1.0); m = meta[[mm['name'] for mm in meta].index(n)]; cx_, cy_ = corr.get(n, (0.0, 0.0))
        rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x'] + cx_).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y'] + cy_).astype(np.float32)
        vv = dict(v); vv['sol_x'] = v['sol_x'] + cx_; vv['sol_y'] = v['sol_y'] + cy_; fl = f2.mascara_lluna(ctx, vv, rx, ry)
        plans = ctx.plans(n, v['exp'])
        for i, (pl, w) in plans.items():
            c = comu.IDX_CANAL[i]; oy, ox = ctx.orig[i]
            if fcorr is not None: pl = pl * fcorr[i]
            mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
            dd = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
            nn = cv2.remap(pl * w * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
            b = float(m['offset_RGB'][c])
            if b != 0.0: nn += b * dd
            phi = B.upsample(phis[B.CHN[c]][j]); nn *= np.exp(-phi)
            num[..., c] += nn; den[..., c] += dd; del dd, nn, phi
        applied.append({'name': n, 'exp': v['exp'], 'k': k, 'correccio_sol_px': [cx_, cy_]}); log(f'{group} {n} ({time.time() - t0:.0f}s)'); del rx, ry, fl, plans
    cam = np.where(den > 0, num / np.maximum(den, 1e-20), np.nan); del num
    _, total = comu.lluminancia(cam, run.matriu, run.color['guany']); del cam; total = total.astype(np.float32)
    out = CAU42 / f'{group}_total_v42{sufix}.npy'; np.save(out, total); np.save(CAU42 / f'{group}_weights_v42{sufix}.npy', den.astype(np.float32))
    savejson(REB42 / f'B2_{group}{sufix}.json', {'group': group, 'delta_arcmin': math.degrees(delta) * 60, 'correccions': corr, 'frames': applied, 'flat_ripple_correction': frep, 'sortida': str(out), 'sha256': sha(out)})
    log(f'B2 V42 fet: {out}')


if __name__ == '__main__':
    main()
