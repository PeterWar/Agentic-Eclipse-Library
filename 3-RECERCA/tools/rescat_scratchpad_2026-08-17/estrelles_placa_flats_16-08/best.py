"""Guany a partir nomes de les parelles netes (dt curt, escena estatica)."""
import numpy as np, ptc2, analyse as A, combine as C, sys, json, time

VD = '/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/'
SD = '/Users/USUARI/Desktop/Eclipse 2026/300mm/'

BEST = {
    'vixen': [('1/125', VD + '572A2999.CR3', VD + '572A3005.CR3', 6.06),
              ('1/30', VD + '572A3000.CR3', VD + '572A3006.CR3', 6.07),
              ('1/8', VD + '572A3001.CR3', VD + '572A3007.CR3', 6.07),
              ('0.5', VD + '572A3002.CR3', VD + '572A3008.CR3', 6.07),
              ('2', VD + '572A2979.CR3', VD + '572A2980.CR3', 2.90),
              ('2b', VD + '572A2980.CR3', VD + '572A2981.CR3', 2.91),
              ('10.3', VD + '572A2982.CR3', VD + '572A2983.CR3', 13.07),
              ('10.3b', VD + '572A2983.CR3', VD + '572A2984.CR3', 13.40)],
    'sony': [('1/6400', SD + 'DSC06974.ARW', SD + 'DSC06977.ARW', 3.0),
             ('1/800', SD + 'DSC06973.ARW', SD + 'DSC06976.ARW', 3.0),
             ('1/100', SD + 'DSC06975.ARW', SD + 'DSC06978.ARW', 3.0),
             ('1/100b', SD + 'DSC07002.ARW', SD + 'DSC07005.ARW', 4.0),
             ('1/30', SD + 'DSC06995.ARW', SD + 'DSC06998.ARW', 5.5),
             ('1/4', SD + 'DSC06994.ARW', SD + 'DSC06997.ARW', 5.0),
             ('2', SD + 'DSC06996.ARW', SD + 'DSC06999.ARW', 5.5),
             ('1/1000', SD + 'DSC06939.ARW', SD + 'DSC06940.ARW', 2.0)],
}


def run(cam, chan='G1', box=24, order=2, q=0.25, verbose=True):
    dof = box * box - (order + 1) * (order + 2) // 2
    gs, es, rows = [], [], []
    for exp, pa, pb, dt in BEST[cam]:
        a = ptc2.plane(pa, chan); b = ptc2.plane(pb, chan)
        sh, _ = ptc2.measure_shift(a, b, 512.0)
        dy, dx = int(round(sh[0])), int(round(sh[1]))
        if dy or dx:
            b = np.roll(np.roll(b, dy, 0), dx, 1)
        m = 8 + max(abs(dy), abs(dx))
        S, V, Vm, St = ptc2.patch_table(a[m:-m, m:-m], b[m:-m, m:-m], 512.0, box=box, order=order)
        bb = A.ptc_bins(S, V, dof, nb=18, smin=max(0.8, np.percentile(S, 2)), smax=S.max(), q=q, minn=40)
        if len(bb) < 6:
            continue
        f = A.fitline(bb)
        gs.append(f['g']); es.append(f['dg'])
        rows.append((exp, f['g'], f['dg'], f['rn'], bb[0, 0], bb[-1, 0], sh))
        if verbose:
            print(f'  {exp:>7s} g={f["g"]:6.3f}+-{f["dg"]:5.3f} RN={f["rn"]:5.2f} S=[{bb[0,0]:7.1f},{bb[-1,0]:8.0f}] sh=({sh[0]:+.2f},{sh[1]:+.2f})', flush=True)
    g, e, chi2, n = C.combine(gs, es)
    return g, e, chi2, n, rows


if __name__ == '__main__':
    cam = sys.argv[1]
    for chan in ['G1', 'G2', 'R', 'B']:
        t = time.time()
        print(f'--- {cam} canal {chan} box24 order2 q0.25')
        g, e, c2, n, _ = run(cam, chan)
        print(f'  => g = {g:.4f} +- {e:.4f} e/ADU (chi2red={c2:.2f}, {n} parelles) [{time.time()-t:.0f}s]', flush=True)
    for box, order, q in [(16, 2, .25), (32, 2, .25), (24, 3, .25), (24, 2, .10), (24, 2, .50), (48, 3, .25)]:
        print(f'--- {cam} G1 box{box} order{order} q{q}')
        g, e, c2, n, _ = run(cam, 'G1', box, order, q, verbose=False)
        print(f'  => g = {g:.4f} +- {e:.4f} e/ADU (chi2red={c2:.2f}, {n})', flush=True)
