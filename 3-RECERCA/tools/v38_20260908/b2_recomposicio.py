"""B2 (V38) · Com la V36 MÉS la correcció mesurada (A1/A2 V38) del dèficit de llum de cada fotograma prop de la SEVA vora lunar: nn *= exp(−B_classe(d)), amb d la distància a la vora lunar modelada del fotograma i B la taula cau/correccio_vora_lunar.json (mediana de ln(fotograma/compost net) per classe d'exposició; 0 més enllà de 30 px). Només Vixen (la Sony no entra a < 1,9 R☉).

Heretat de B2 (V36) · Recomposició LDIC a resolució completa amb la finestra gradual, la linealitat Sony, els camps B1 (V34) i el flat Sony suavitzat.

Idèntic a `v29/prepare_final_grid.py` (mateix registre F1.3, mateixos pesos
`f2.finestra`, mateixa màscara lunar, mateix guany k, un sol remostreig bilineal
del subpla CFA a la graella final) amb DUES diferències declarades:
  · cada subpla entra multiplicat per exp(−φ_i,c(x)) (camp suau de B1, per fotograma
    i canal natiu, remostrejat de la graella 1/4 a la completa);
  · l'offset additiu del c03 (b_i,c) hi entra també, com a `apply_offsets.py`
    (Σ w·b / Σ w), abans del camp: L = (pl·k + b)·exp(−φ).
Els pesos (den) han de coincidir amb els de la V29: es comprova i s'anota.
Sortida: cau/{grup}_total_v32.npy (H,W,3) en sRGB lineal (matriu i guany del run),
com `{grup}_total.npy` de la V29. Només lectura sobre RAW i runs.
"""
from comu38 import *
TAULA = json.loads((CAU38 / 'correccio_vora_lunar.json').read_text())['taula']
def classe(e):
    return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
def correccio_vora(D, e):
    tb = TAULA[classe(e)]; B = np.interp(D, np.asarray(tb['d_px'], np.float32), np.asarray(tb['B_ln'], np.float32), left=tb['B_ln'][0], right=0.0).astype(np.float32); return np.exp(-B, dtype=np.float32)


GROUPS = {'vixen': ('vixen', None), 'sony_A': ('sony', 'sony_A'), 'sony_B': ('sony', 'sony_B')}
CHN = {0: 'R', 1: 'G', 2: 'B'}


def upsample(phi_c):
    """(HC,WC) → (H,W): cel·les centrades a (4j+1,5); vora replicada per als 2-3 px sobrants."""
    a = cv2.resize(np.asarray(phi_c, np.float32), (WC * Q, HC * Q), interpolation=cv2.INTER_LINEAR)
    out = np.empty((H, W), np.float32); out[:HC * Q, :WC * Q] = a
    out[HC * Q:, :WC * Q] = a[-1:, :]; out[:, WC * Q:] = out[:, WC * Q - 1:WC * Q]
    return out


def main():
    inv = cv2.invertAffineTransform(COMMON_TO_FINAL)
    yy, xx = np.ogrid[:H, :W]
    qx = (inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]).astype(np.float32); qy = (inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]).astype(np.float32)
    rep = {}
    only = [a for a in sys.argv[1:] if a in GROUPS]
    for group, (tag, grp) in GROUPS.items():
        if only and group not in only:
            continue
        path = RUNS[tag]; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run)
        pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']
        kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']
        meta = json.loads((CAU36 / f'{tag}_meta.json').read_text())['frames']
        names = [m['name'] for m in meta if (grp is None or m['group'] == grp)]
        b1 = json.loads((REB36 / f'B1_camps_{group}.json').read_text()); assert b1['frames'] == names
        phis = {c: np.load(CAU36 / f'{group}_{c}_phi.npy', mmap_mode='r') for c in ('R', 'G', 'B')}
        fcorr, frep = flat_ripple_correction(ctx, tag)
        if fcorr is not None:
            log(f'{group}: correcció de l\'ondulació del flat: ' + ' · '.join(f"subpla {i}: rms {frep[str(i)]['ripple_rms_pct_r400_2400']:.3f}%" for i in range(4)))
        num = np.zeros((H, W, 3), np.float32); den = np.zeros((H, W, 3), np.float32)
        dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
        t0 = time.time(); applied = []
        for j, n in enumerate(names):
            v = pos[n]; k = kq.get(n, 1.0); m = meta[[mm['name'] for mm in meta].index(n)]
            rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x']).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y']).astype(np.float32)
            fl = f2.mascara_lluna(ctx, v, rx, ry)
            mlx = v['sol_x'] + float(v['lluna_dx']); mly = v['sol_y'] + float(v['lluna_dy']); corr = correccio_vora(np.hypot(rx - mlx, ry - mly) - ctx.RL, v['exp']) if tag == 'vixen' else None   # V38
            # (V36c) l'esvaïment espacial dels 8 s es va provar i REFUSAR (bony de gra +30 % en 1200 px): pesos com la V35
                # fl = fl * taper_8s(coarse=False)          # V36: entrada espacial gradual dels 8 s
            plans = ctx.plans(n, v['exp'])
            for i, (pl, w) in plans.items():
                c = comu.IDX_CANAL[i]; oy, ox = ctx.orig[i]
                if fcorr is not None:
                    pl = pl * fcorr[i]                                # flat sense ondulació radial (A6)
                mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
                dd = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
                nn = cv2.remap(pl * w * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
                b = float(m['offset_RGB'][c])
                if b != 0.0:
                    nn += b * dd                                  # offset c03 a través dels mateixos pesos
                phi = upsample(phis[CHN[c]][j]); nn *= np.exp(-phi)   # camp de nivell per fotograma i canal
                if corr is not None:
                    nn *= corr                                           # V38: dèficit prop de la vora lunar del fotograma
                num[..., c] += nn; den[..., c] += dd
                del dd, nn, phi
            applied.append({'name': n, 'exp': v['exp'], 'k': k, 'offset_RGB': m['offset_RGB'], 'classe_vora': classe(v['exp']) if tag == 'vixen' else None})
            if j % 10 == 0 or j == len(names) - 1:
                log(f'{group} {j+1}/{len(names)} ({time.time()-t0:.0f}s)')
            del rx, ry, fl, plans, corr
        cam = np.where(den > 0, num / np.maximum(den, 1e-20), np.nan); del num
        # comprovació: els pesos són els de la V29 (mateixa cadena, mateixos fotogrames)
        ref = np.load(CAUF / f'{group}_weights.npy', mmap_mode='r')
        sl = (slice(0, H, 7), slice(0, W, 7)); d_ref = np.asarray(ref[sl]); d_new = den[sl]
        ok = (d_ref > 0) | (d_new > 0); rel = np.max(np.abs(d_new[ok] - d_ref[ok]) / np.maximum(d_ref[ok], 1e-6))
        # V34: els pesos SÓN diferents dels de la V29 (finestra gradual): s'anota, no s'exigeix
        _, total = comu.lluminancia(cam, run.matriu, run.color['guany']); del cam
        total = total.astype(np.float32)
        np.save(CAU38 / f'{group}_total_v38.npy', total)
        old = np.load(CAUF / f'{group}_total.npy', mmap_mode='r')
        good = np.all(np.isfinite(total[sl]) & (total[sl] > 0), axis=2) & np.all(np.isfinite(np.asarray(old[sl])) & (np.asarray(old[sl]) > 0), axis=2)
        lr = np.log(total[sl][good] / np.asarray(old[sl])[good])
        rep[group] = {'frames': applied, 'flat_ripple_correction': frep, 'weights_max_rel_diff_vs_V29': float(rel), 'ln_total_v32_over_v29_p1_p50_p99_per_channel': [[float(np.percentile(lr[:, c], q)) for q in (1, 50, 99)] for c in range(3)],
                      'sha256': sha(CAU38 / f'{group}_total_v38.npy')}
        log(f'{group}: pesos idèntics (max rel {rel:.2e}); ln(v32/v29) p1/p50/p99 G = {rep[group]["ln_total_v32_over_v29_p1_p50_p99_per_channel"][1]}')
        del total, den, ctx
    prev = REB38 / 'B2_recomposicio.json'
    if prev.exists():
        old = json.loads(prev.read_text()); old.update(rep); rep = old
    savejson(REB38 / 'B2_recomposicio.json', rep)
    log('B2 fet')


if __name__ == '__main__':
    main()
