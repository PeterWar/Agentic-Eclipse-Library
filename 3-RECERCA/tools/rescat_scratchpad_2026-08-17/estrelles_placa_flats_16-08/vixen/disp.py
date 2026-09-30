import numpy as np, lib, esf
from scipy.optimize import least_squares

NAMES = ["572A2999.CR3", "572A2987.CR3", "572A3005.CR3", "572A2998.CR3",
         "572A3004.CR3", "572A2992.CR3", "572A2974.CR3", "572A2993.CR3",
         "572A3000.CR3", "572A2988.CR3", "572A2991.CR3", "572A2973.CR3"]

acc = {k: [] for k in ('R', 'G1', 'G2', 'B')}
cen = {k: [] for k in ('R', 'G1', 'G2', 'B')}
for name in NAMES:
    img = lib.load(name)
    geo = lib.solve_geometry(img)[:3]
    _, _, out = esf.measure_frame('', keys=('R', 'G1', 'G2', 'B'), nsec=240, img=img, geo=geo)
    for k in acc:
        rr = out[k]['rows']
        s = np.array([x['sigma'] for x in rr]); a = np.array([x['amp'] for x in rr])
        rm = np.array([x['rms'] for x in rr]); th = np.array([x['th'] for x in rr])
        r0 = np.array([x['r0'] for x in rr])
        g = (a/np.maximum(rm, 1e-9) > 15) & (s > 0.2) & (s < 8)
        acc[k].append((th[g], s[g]))
        # centre relatiu: r0 = dR + dy*cos(th) + dx*sin(th)
        A = np.column_stack([np.ones(g.sum()), np.cos(th[g]), np.sin(th[g])])
        w = np.ones(g.sum())
        for _ in range(4):
            sol, *_ = np.linalg.lstsq(A*w[:, None], r0[g]*w, rcond=None)
            res = r0[g] - A@sol
            sd = 1.4826*np.median(np.abs(res - np.median(res)))
            w = (np.abs(res-np.median(res)) < 2.5*sd).astype(float)
        cen[k].append(sol)   # dR, dy, dx en px raw

print("=== desplacament del centre per canal (px raw, respecte del cercle comu) ===")
print("th=0 es +y (files creixents); dy=+y, dx=+x")
base = np.mean([np.array(cen[k]) for k in ('G1', 'G2')], axis=0)
for k in ('R', 'G1', 'G2', 'B'):
    c = np.array(cen[k])
    d = c - base
    print("%3s  dR=%+.3f+-%.3f  dy=%+.3f+-%.3f  dx=%+.3f+-%.3f   (relatiu a G)" % (
        k, d[:, 0].mean(), d[:, 0].std(ddof=1)/np.sqrt(len(d)),
        d[:, 1].mean(), d[:, 1].std(ddof=1)/np.sqrt(len(d)),
        d[:, 2].mean(), d[:, 2].std(ddof=1)/np.sqrt(len(d))))
rb = np.array(cen['R']) - np.array(cen['B'])
print("R-B: dy=%+.3f+-%.3f px  dx=%+.3f+-%.3f px  -> modul %.3f px = %.2f arcsec" % (
    rb[:, 1].mean(), rb[:, 1].std(ddof=1)/np.sqrt(len(rb)),
    rb[:, 2].mean(), rb[:, 2].std(ddof=1)/np.sqrt(len(rb)),
    np.hypot(rb[:, 1].mean(), rb[:, 2].mean()),
    np.hypot(rb[:, 1].mean(), rb[:, 2].mean())*lib.SCALE))
ang = np.degrees(np.arctan2(rb[:, 2].mean(), rb[:, 1].mean()))
print("   direccio R-B: %.1f graus des de +y cap a +x" % ang)

print()
print("=== sigma^2 vs azimut:  s^2 = a + b*cos^2(th - th0) ===")
for k in ('R', 'G1', 'G2', 'B'):
    th = np.concatenate([t for t, s in acc[k]])
    s = np.concatenate([s for t, s in acc[k]])
    def f(p):
        a, b, t0 = p
        return a + b*np.cos(th - t0)**2 - s**2
    r = least_squares(f, [np.median(s)**2, 0.1, 0.0], loss='soft_l1', f_scale=0.3)
    a, b, t0 = r.x
    t0d = np.degrees(t0) % 180
    fw_min = 2.3548*np.sqrt(max(a, 1e-6))*lib.SCALE
    fw_max = 2.3548*np.sqrt(max(a+b, 1e-6))*lib.SCALE
    print("%3s  FWHM min=%.2f\"  max=%.2f\"  eix llarg a %.1f deg   (b=%.4f px^2)" %
          (k, fw_min, fw_max, t0d, b))
    # perfil per bins
    bins = np.linspace(-np.pi, np.pi, 13)
    prof = [np.median(s[(th >= bins[i]) & (th < bins[i+1])]) for i in range(12)]
    print("     FWHM per sector de 30 deg:", " ".join("%.1f" % (2.3548*p*lib.SCALE) for p in prof))
np.save("acc_disp.npy", np.array([1]))
