"""Corba de linealitat de cada sensor, mesurada de la dada: per parelles d'exposicions veïnes i en
dos sectors, ln(pl_llarg·k_l·e^{−φ_l} + b_l) − ln(pl_curt·k_c·e^{−φ_c} + b_c) en calaixos de
x = (DN_llarg − pedestal)/(saturació − pedestal), amb el curt a l'altiplà lineal (x_curt < 0,6, DN > 300).
Resolució completa (ROI), subpla G. Ajust: L(x) = 1 − a·max(0, x − x0)^2 per sensor."""
import os, sys, json
from pathlib import Path
os.environ['V29_FINAL_GRID'] = '1'
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026'); sys.path.insert(0, str(ROOT / 'research/tools/v32_arcs_20260907')); from comu32 import *
import f2, rawpy
from b2_recomposicio import upsample
OUT = ROOT / 'output/revisio_marques_v33_20260907'; VISd = OUT / 'lliurables/vistes'; REBd = OUT / '4-rebuts'
XB = np.arange(0.30, 1.001, 0.05)
SECTORS = [110.0, -50.0, 30.0]
PAIRS = {'vixen': [('572A2982.CR3', '572A2979.CR3'), ('572A2983.CR3', '572A2980.CR3'), ('572A2984.CR3', '572A2981.CR3'), ('572A2979.CR3', '572A2996.CR3'), ('572A2980.CR3', '572A2978.CR3'), ('572A2996.CR3', '572A3002.CR3'), ('572A2978.CR3', '572A3008.CR3')],
         'sony': [('DSC06993.ARW', 'DSC06996.ARW'), ('DSC06993.ARW', 'DSC06999.ARW'), ('DSC06996.ARW', 'DSC06991.ARW'), ('DSC06999.ARW', 'DSC06991.ARW')]}


def main():
    res = {}
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.5))
    for ai, tag in enumerate(('vixen', 'sony')):
        path = RUNS[tag]; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run); pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']
        meta = {m['name']: m for m in json.loads((CAU32 / f'{tag}_meta.json').read_text())['frames']}
        grp = 'vixen' if tag == 'vixen' else 'sony_B'; b1 = json.loads((ROOT / 'output/v32_arcs_20260907/4-rebuts' / f'B1_camps_{grp}.json').read_text())['frames']; phi = np.load(CAU32 / f'{grp}_G_phi.npy', mmap_mode='r')
        ped, sat = ctx.cfg['pedestal_dn'], ctx.cfg['saturacio_dn']; gi = [i for i in range(4) if comu.IDX_CANAL[i] == 1][0]; oy, ox = ctx.orig[gi]
        acc = {}
        for AZ in SECTORS:
            cx0 = CX + 1.8 * RS * np.cos(np.radians(AZ)); cy0 = CY + 1.8 * RS * np.sin(np.radians(AZ)); half = 480
            x0, x1, y0, y1 = int(cx0 - half), int(cx0 + half), int(cy0 - half), int(cy0 + half)
            inv = cv2.invertAffineTransform(COMMON_TO_FINAL); yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            qx = (inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]).astype(np.float32); qy = (inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]).astype(np.float32); dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
            cache = {}
            def get(n):
                if n in cache:
                    return cache[n]
                v = pos[n]; e = v['exp']; rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x']).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y']).astype(np.float32)
                with rawpy.imread(ctx.ruta[n]) as r:
                    raw = r.raw_image.astype(np.float32)
                dk = ctx.dark(e); sub = raw[oy::2, ox::2]; pl = comu.calibra_pla(sub, dk[oy::2, ox::2], ctx.flat[oy::2, ox::2], e, ctx.wb, ctx.mc, gi); xrel = (sub - ped) / (sat - ped)
                mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
                P = cv2.remap(pl, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); X = cv2.remap(xrel, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
                ph = upsample(np.asarray(phi[b1.index(n)]))[y0:y1, x0:x1] if n in b1 else 0.0
                val = (P * kq.get(n, 1.0) + meta[n]['offset_RGB'][1]) * np.exp(-ph)
                cache[n] = (val, X, e); return cache[n]
            for a, b in PAIRS[tag]:
                if a not in pos or b not in pos:
                    continue
                va, xa, ea = get(a); vb, xb, eb = get(b)
                ok = (xa > 0.25) & (xa < 1.02) & (xb > 0.02) & (xb < 0.60) & (va > 0) & (vb > 0) & ((xb * (sat - ped)) > 300)
                d = np.log(va / vb)
                for i in range(len(XB) - 1):
                    k = ok & (xa >= XB[i]) & (xa < XB[i + 1])
                    if k.sum() > 300:
                        acc.setdefault(f'{ea:g}/{eb:g}', {}).setdefault(i, []).append(float(np.median(d[k])))
            log(f'{tag} sector {AZ} fet')
        curve = {}; xs = 0.5 * (XB[:-1] + XB[1:])
        allbins = {i: [] for i in range(len(XB) - 1)}
        for pair, bins in acc.items():
            med = [float(np.median(bins[i])) if i in bins else np.nan for i in range(len(XB) - 1)]
            # referència: el valor a x 0,30–0,55 (zona lineal comuna) → 0
            ref = np.nanmedian([m for i, m in enumerate(med) if xs[i] < 0.55])
            rel = [m - ref if np.isfinite(m) else np.nan for m in med]; curve[pair] = rel
            for i, v in enumerate(rel):
                if np.isfinite(v):
                    allbins[i].append(v)
            axs[ai].plot(xs, 100 * np.array(rel), marker='o', ms=3, lw=.8, label=pair)
        L = np.array([np.median(allbins[i]) if allbins[i] else np.nan for i in range(len(XB) - 1)])
        # ajust L(x) = -a·max(0,x−x0)² en ln (a partir de la mediana de parelles)
        ok = np.isfinite(L); best = None
        for x0_ in np.arange(0.45, 0.85, 0.01):
            X_ = np.maximum(0, xs[ok] - x0_) ** 2
            if X_.sum() == 0:
                continue
            a_ = -np.sum(X_ * L[ok]) / np.sum(X_ * X_); err = np.sum((L[ok] + a_ * X_) ** 2)
            if best is None or err < best[0]:
                best = (err, x0_, a_)
        err, x0_, a_ = best; fit = -a_ * np.maximum(0, xs - x0_) ** 2
        axs[ai].plot(xs, 100 * L, 'k', lw=2, label='mediana de parelles'); axs[ai].plot(xs, 100 * fit, 'r--', lw=1.5, label=f'ajust: −{a_:.3f}·max(0,x−{x0_:.2f})²')
        axs[ai].axhline(0, color='.5', lw=.5); axs[ai].axvline(0.7, color='orange', lw=.8, ls=':'); axs[ai].axvline(0.85, color='orange', lw=.8, ls=':'); axs[ai].set_xlabel('x = (DN − pedestal)/(saturació − pedestal) del fotograma LLARG'); axs[ai].set_ylabel('ln(llarg/curt) − referència [%]'); axs[ai].set_title(f'{tag}: linealitat del sensor prop de la saturació (subpla G, {len(SECTORS)} sectors)', fontsize=9); axs[ai].legend(fontsize=6, ncol=2); axs[ai].set_ylim(-3, 1)
        res[tag] = {'x_centres': xs.tolist(), 'per_parella_pct': {k: [None if np.isnan(v) else 100 * v for v in vv] for k, vv in curve.items()}, 'mediana_pct': [None if np.isnan(v) else 100 * v for v in L], 'ajust': {'forma': 'ln L(x) = -a*max(0, x-x0)^2', 'a': float(a_), 'x0': float(x0_), 'err': float(err)}, 'pedestal_dn': ped, 'saturacio_dn': sat}
        print(tag, 'mediana %:', [None if np.isnan(v) else round(100 * v, 2) for v in L], '| ajust a', round(a_, 4), 'x0', round(x0_, 2))
    fig.tight_layout(); fig.savefig(VISd / 'R33_linealitat_sensor.png', dpi=120); savejson(REBd / 'R33_linealitat_sensor.json', res); log('linealitat feta')


if __name__ == '__main__':
    main()
