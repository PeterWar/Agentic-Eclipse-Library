import sys, json, math, numpy as np
sys.path.insert(0, '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
from esfcmp import *
from run import TRAINS


def measure(train, name, chan='G', nsec=240, align=True, win_as=30.0, xlim_as=20.0,
            addnoise=0.0, nazgrp=0):
    t = TRAINS[train]
    v, c, white = load(t['dirp'] + name + t['ext'])
    if addnoise > 0:
        rng = np.random.default_rng(7)
        v = v + rng.normal(0, addnoise, v.shape)
    x, y, val = pick(v, c, chan)
    cx, cy, R = centroid(v)
    for w in (60.0, 25.0):
        cx, cy, R, sd, ng = fit_circle(x, y, val, cx, cy, R, win=w)
    fits = sector_fits(x, y, val, cx, cy, R, win_as / t['scale'], nsec, (white - 512) * 0.93)
    if len(fits) < 20:
        return None
    xc, ym, e, cnt = stack_esf(fits, align=align, xlim=xlim_as / t['scale'], bw=0.05)
    f = fit_esf(xc, ym, e, boxw=1.0)
    out = dict(fwhm=f['fwhm_tot'] * t['scale'], snr=float(np.median([q['snr'] for q in fits])),
               nok=len(fits), chi2=f['chi2'])
    if nazgrp:
        # anisotropia: sigma^2 equivalent per grup azimutal
        g = []
        for k in range(nazgrp):
            sub = [q for q in fits if (q['a'] * nazgrp) // nsec == k]
            if len(sub) < 8:
                continue
            x2, y2, e2, _ = stack_esf(sub, align=align, xlim=xlim_as / t['scale'], bw=0.15)
            f2 = fit_esf(x2, y2, e2, boxw=1.0)
            g.append((2 * math.pi * (k + 0.5) / nazgrp, f2['fwhm_tot'] * t['scale']))
        th = np.array([q[0] for q in g]); fw = np.array([q[1] for q in g])
        s2 = (fw / 2.3548) ** 2
        A = np.stack([np.ones_like(th), np.cos(2 * th), np.sin(2 * th)], 1)
        sol, *_ = np.linalg.lstsq(A, s2, rcond=None)
        b = math.hypot(sol[1], sol[2])
        th0 = 0.5 * math.degrees(math.atan2(sol[2], sol[1])) % 180
        out['aniso'] = dict(fw_min=2.3548 * math.sqrt(max(sol[0] - b, 1e-6)),
                            fw_max=2.3548 * math.sqrt(sol[0] + b), pa=th0,
                            per=[(round(math.degrees(q[0])), round(q[1], 2)) for q in g])
    return out


if __name__ == '__main__':
    what = sys.argv[1]
    if what == 'noise':
        # biaix per soroll: degradar un fotograma bo fins a la S/N dels curts
        for train, name in [('vixen', '572A2999'), ('sony', 'DSC06995')]:
            for n in (0.0, 15.0, 40.0, 90.0, 200.0):
                r = measure(train, name, addnoise=n)
                print(f"{train:5s} {name} soroll+{n:5.0f} ADU  S/N={r['snr']:5.1f}  FWHM={r['fwhm']:.2f}\"", flush=True)
    elif what == 'aniso':
        for train, names in [('vixen', ['572A2987', '572A2999', '572A2974']),
                             ('sony', ['DSC06983', 'DSC06995', 'DSC06981'])]:
            for name in names:
                for ch in ('R', 'G', 'B'):
                    r = measure(train, name, chan=ch, nazgrp=12)
                    a = r['aniso']
                    print(f"{train:5s} {name} {ch}  FWHM={r['fwhm']:.2f}\"  min={a['fw_min']:.2f}\" "
                          f"max={a['fw_max']:.2f}\" PA={a['pa']:.0f}deg  raó={a['fw_max']/max(a['fw_min'],1e-3):.2f}", flush=True)
    elif what == 'expo':
        V = [('572A2985', '1/2000'), ('572A2986', '1/500'), ('572A2987', '1/125'),
             ('572A2988', '1/30'), ('572A2989', '1/8'),
             ('572A2997', '1/2000'), ('572A2998', '1/500'), ('572A2999', '1/125'),
             ('572A3000', '1/30'), ('572A3001', '1/8'),
             ('572A3003', '1/2000'), ('572A3004', '1/500'), ('572A3005', '1/125'),
             ('572A3006', '1/30'), ('572A3007', '1/8'),
             ('572A2963', '1/3200'), ('572A2964', '1/3200'), ('572A3020', '1/3200'),
             ('572A3021', '1/3200'), ('572A3040', '1/3200'), ('572A3041', '1/3200')]
        for n, e in V:
            r = measure('vixen', n)
            if r:
                print(f"vixen {n} {e:7s} FWHM={r['fwhm']:.2f}\" S/N={r['snr']:.0f} nok={r['nok']}", flush=True)
        S = [('DSC06979', '1/800'), ('DSC06981', '1/100'), ('DSC06983', '1/30'),
             ('DSC06976', '1/800'), ('DSC06978', '1/100'),
             ('DSC07000', '1/800'), ('DSC07002', '1/100'), ('DSC06995', '1/30'),
             ('DSC06973', '1/800'), ('DSC06975', '1/100'), ('DSC06980', '1/6400'),
             ('DSC06977', '1/6400'), ('DSC07001', '1/6400')]
        for n, e in S:
            r = measure('sony', n)
            if r:
                print(f"sony  {n} {e:7s} FWHM={r['fwhm']:.2f}\" S/N={r['snr']:.0f} nok={r['nok']}", flush=True)
