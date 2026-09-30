import numpy as np, ptc2, limb, prom, sys, json
from scipy.ndimage import shift as ndshift

def disc_of(path, guess=None, chan='G1'):
    g = ptc2.plane(path, chan)
    if guess is None:
        d = limb.find_disc(g)
        cy, cx, r = d
    else:
        cy, cx, r = guess
    return limb.refine_disc(g, cy, cx, r)

def cut(img, cy, cx, R, azdeg, r0=-4, r1=30, halfaz=11.0, pad=4):
    aa = np.radians(np.linspace(azdeg - halfaz, azdeg + halfaz, 80))
    ys = np.concatenate([cy + (R + r) * np.sin(aa) for r in (r0, r1)])
    xs = np.concatenate([cx + (R + r) * np.cos(aa) for r in (r0, r1)])
    y0, y1 = int(ys.min()) - pad, int(ys.max()) + pad
    x0, x1 = int(xs.min()) - pad, int(xs.max()) + pad
    return y0, y1, x0, x1

def analyse(cam, files, azlist, g, rn_adu, scale_arcsec, chans=('R', 'G1', 'B')):
    """files: [(fitxer_a, fitxer_b, exp_txt, t_s)] parelles de la mateixa exposicio."""
    out = {}
    ref = files[0][0]
    d0 = disc_of(ref)
    print(f'{cam}: disc de referencia cy={d0[0]:.2f} cx={d0[1]:.2f} R={d0[2]:.2f} px_pla '
          f'({d0[2]*2*scale_arcsec:.0f} arcsec de radi)')
    for pa, pb, exp, t in files:
        da = disc_of(pa, guess=d0[:3]); db = disc_of(pb, guess=d0[:3])
        for chan in chans:
            A = ptc2.plane(pa, chan) - 512.0
            B = ptc2.plane(pb, chan) - 512.0
            # alinea B sobre A pel limbe lunar (subpixel)
            B = ndshift(B, (da[0] - db[0], da[1] - db[1]), order=3, mode='nearest')
            cy, cx, R = da[0], da[1], da[2]
            for az in azlist:
                y0, y1, x0, x1 = cut(A, cy, cx, R, az)
                a = A[y0:y1, x0:x1]; b = B[y0:y1, x0:x1]
                M = (a + b) / 2.0
                D = a - b
                msk = prom.radial_mask(a.shape, y0, x0, cy, cx, R, 1.0, 26.0, az, 9.0)
                sat = float(np.mean(np.maximum(a, b)[msk] > 15300))
                key = (exp, chan, az)
                out[key] = dict(S=M[msk], D=D[msk], box=(y0, y1, x0, x1), sat=sat,
                                A=a, B=b, mask=msk, cy=cy, cx=cx, R=R, t=t)
    return out
