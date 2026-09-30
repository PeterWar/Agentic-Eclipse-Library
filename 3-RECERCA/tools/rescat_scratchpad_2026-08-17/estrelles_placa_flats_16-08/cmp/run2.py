import sys, json, math, numpy as np
sys.path.insert(0, '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
from esfcmp import *
from run import TRAINS


def prep(train, name, chan='G', nsec=240, win_as=30.0):
    t = TRAINS[train]
    v, c, white = load(t['dirp'] + name + t['ext'])
    x, y, val = pick(v, c, chan)
    cx, cy, R = centroid(v)
    for w in (60.0, 25.0):
        cx, cy, R, sd, ng = fit_circle(x, y, val, cx, cy, R, win=w)
    fits = sector_fits(x, y, val, cx, cy, R, win_as / t['scale'], nsec, (white - 512) * 0.93)
    return t, fits, dict(cx=cx, cy=cy, R=R)


def full(train, name, chan='G', nsec=240, align=True, win_as=30.0, xlim_as=20.0,
         nazgrp=0, noise=0.0, bw=0.05):
    t, fits, geo = prep(train, name, chan, nsec, win_as)
    if len(fits) < 20:
        return None
    res = dict(train=train, frame=name, chan=chan, nsec=nsec, align=align,
               nsec_ok=len(fits), R_as=geo['R'] * t['scale'])
    xc, ym, e, cnt = stack_esf(fits, align=align, xlim=xlim_as / t['scale'], bw=bw)
    f = fit_esf(xc, ym, e, boxw=1.0)
    res['fwhm_tot_as'] = f['fwhm_tot'] * t['scale']
    res['fwhm_int_as'] = f['fwhm_int'] * t['scale']
    res['chi2'] = f['chi2']
    res['esf'] = dict(x_as=(xc * t['scale']).tolist(), y=ym.tolist(),
                      e=e.tolist(), fit=[f['a'], f['s1'] * t['scale'], f['s2'] * t['scale']])
    if nazgrp:
        per = []
        for g in range(nazgrp):
            sub = [q for q in fits if (q['a'] * nazgrp) // nsec == g]
            if len(sub) < 8:
                per.append(None); continue
            xc2, ym2, e2, _ = stack_esf(sub, align=align, xlim=xlim_as / t['scale'], bw=bw*3)
            f2 = fit_esf(xc2, ym2, e2, boxw=1.0)
            per.append(dict(g=g, th=360.0 * (g + 0.5) / nazgrp,
                            fwhm=f2['fwhm_tot'] * t['scale'], n=len(sub)))
        res['azim'] = per
    return res


if __name__ == '__main__':
    jobs = json.loads(sys.argv[1])
    out = []
    for j in jobs:
        try:
            r = full(**j)
        except Exception as ex:
            print('ERR', j, ex, flush=True); continue
        if not r:
            print('SKIP', j, flush=True); continue
        out.append(r)
        line = (f"{r['train']:5s} {r['frame']:10s} {r['chan']} nsec={r['nsec']:3d} "
                f"align={str(r['align']):5s} ok={r['nsec_ok']:3d} FWHM={r['fwhm_tot_as']:.2f}\" "
                f"chi2={r['chi2']:.2f}")
        if r.get('azim'):
            line += ' | az: ' + ' '.join('--' if a is None else f"{a['fwhm']:.1f}" for a in r['azim'])
        print(line, flush=True)
    json.dump(out, open(sys.argv[2], 'w'))
