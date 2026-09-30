import numpy as np, ptc2, limb, prom, scales, sys

CAM = {
    'R6III': dict(dirn=prom.V, ext='.CR3', g=5.08, rn=2.72, scale=2.158,
                  ref='572A2999',
                  frames=[('572A2997', '1/2000'), ('572A2985', '1/2000'), ('572A3003', '1/2000'),
                          ('572A2991', '1/1000'), ('572A2998', '1/500'), ('572A2986', '1/500'),
                          ('572A3004', '1/500'), ('572A2992', '1/250'), ('572A2999', '1/125'),
                          ('572A2987', '1/125'), ('572A3005', '1/125'), ('572A2993', '1/60'),
                          ('572A2988', '1/30'), ('572A3000', '1/30')],
                  az=[189.5, 10.0]),
    'A7RIIIA': dict(dirn=prom.S, ext='.ARW', g=3.41, rn=1.22, scale=3.234,
                    ref='DSC06978',
                    frames=[('DSC06974', '1/6400'), ('DSC06977', '1/6400'), ('DSC06980', '1/6400'),
                            ('DSC07001', '1/6400'),
                            ('DSC06973', '1/800'), ('DSC06976', '1/800'), ('DSC06979', '1/800'),
                            ('DSC07000', '1/800'), ('DSC07003', '1/800'),
                            ('DSC06975', '1/100'), ('DSC06978', '1/100'), ('DSC06981', '1/100'),
                            ('DSC07002', '1/100'), ('DSC07005', '1/100')],
                    az=None),
}


def disc(path):
    g = ptc2.plane(path, 'G1')
    d = limb.find_disc(g)
    return limb.refine_disc(g, *d)


def find_az(path, R, cy, cx, n=2):
    Rc = ptc2.plane(path, 'R'); G = ptc2.plane(path, 'G1')
    rr, az, PR = limb.polar(Rc, cy, cx, R + 1, R + 10, nr=36, naz=2880)
    rr, az, PG = limb.polar(G, cy, cx, R + 1, R + 10, nr=36, naz=2880)
    exc = PR.mean(1) - 1.35 * PG.mean(1)
    from scipy.signal import find_peaks
    p, _ = find_peaks(exc, height=np.percentile(exc, 96), distance=60)
    o = p[np.argsort(-exc[p])[:n]]
    return [float(np.degrees(az[i])) for i in o]
