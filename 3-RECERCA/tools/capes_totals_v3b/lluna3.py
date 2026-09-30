"""El·lipse del limbe per capa (refracció a 9° d'altura: el disc és ~1 % més curt en altura)."""
import json, sys, numpy as np
from scipy import optimize
from lluna2 import halfedges, V2B
def ellipse_fit(px, py):
    # paràmetres: cx, cy, a, b, theta (radians); residu = distància radial normalitzada * radi
    def model(p, ang):
        cx, cy, a, b, th = p
        return cx, cy, a, b, th
    def resid(p):
        cx, cy, a, b, th = p
        dx, dy = px-cx, py-cy
        c, s = np.cos(th), np.sin(th)
        u = dx*c + dy*s; v = -dx*s + dy*c
        rho = np.sqrt((u/a)**2 + (v/b)**2)
        rloc = np.hypot(dx, dy)
        return (rho-1.0)*rloc
    p0 = [px.mean(), py.mean(), 453.0, 451.0, 0.0]
    keep = np.ones(len(px), bool)
    for it in range(20):
        sol = optimize.least_squares(lambda p: resid(p)[keep], p0, loss='soft_l1', f_scale=0.5)
        p0 = sol.x; r = resid(p0); s = 1.4826*np.median(np.abs(r[keep]))
        nk = np.abs(r) < 3.0*max(s, 0.25)
        if (nk == keep).all(): break
        keep = nk
    cx, cy, a, b, th = p0
    if b > a: a, b, th = b, a, th + np.pi/2
    th = (np.degrees(th) + 180) % 180
    return dict(cx=float(cx), cy=float(cy), a=float(a), b=float(b), theta_deg=float(th), rms=float(r[keep].std()), n=int(keep.sum()), n_tot=len(px))
if __name__ == '__main__':
    ids = [int(a) for a in sys.argv[1:]] or [7, 8, 9, 10]
    out = {}
    for i in ids:
        G = np.load(f'{V2B}/src_id{i}_G.npy', mmap_mode='r')
        c = (3577.5, 2273.5)
        for it in range(3):
            az, rad, ins, outs = halfedges(G, c)
            ok = np.isfinite(rad)
            px = c[0] + rad[ok]*np.cos(az[ok]); py = c[1] - rad[ok]*np.sin(az[ok])
            e = ellipse_fit(px, py); c = (e['cx'], e['cy'])
        out[i] = e
        print(i, {k: round(v, 2) if isinstance(v, float) else v for k, v in e.items()}, flush=True)
    json.dump(out, open('lluna3_ellipse.json', 'w'), indent=1)
