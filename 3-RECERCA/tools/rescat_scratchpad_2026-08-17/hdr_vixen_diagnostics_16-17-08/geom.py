import numpy as np, cv2, json
from scipy.ndimage import gaussian_filter, map_coordinates

def limbe(img_g, cx0, cy0, rmin, rmax, n_az=720, sig=2.0, iters=4):
    """centre i radi del limbe = màxim del gradient radial de img_g."""
    g = gaussian_filter(img_g.astype(np.float32), sig)
    cx, cy = cx0, cy0
    for it in range(iters):
        th = np.linspace(0, 2*np.pi, n_az, endpoint=False)
        rr = np.arange(rmin, rmax, 0.5)
        xx = cx + rr[None,:]*np.cos(th)[:,None]
        yy = cy + rr[None,:]*np.sin(th)[:,None]
        prof = map_coordinates(g, [yy, xx], order=1, mode='nearest')
        d = np.gradient(prof, 0.5, axis=1)
        k = np.argmax(np.abs(d), axis=1)      # |dI/dr| màxim
        rl = rr[k]
        px = cx + rl*np.cos(th); py = cy + rl*np.sin(th)
        # ajust algebraic de cercle amb retall robust
        m = np.ones_like(rl, bool)
        for _ in range(3):
            A = np.c_[2*px[m], 2*py[m], np.ones(m.sum())]
            b = px[m]**2 + py[m]**2
            sol, *_ = np.linalg.lstsq(A, b, rcond=None)
            cx_, cy_ = sol[0], sol[1]; R = np.sqrt(sol[2] + cx_**2 + cy_**2)
            res = np.hypot(px-cx_, py-cy_) - R
            mad = np.median(np.abs(res[m]-np.median(res[m])))*1.4826
            m = np.abs(res) < max(3*mad, 0.5)
        cx, cy = cx_, cy_
    return dict(cx=float(cx), cy=float(cy), R=float(R), n_ok=int(m.sum()), n=int(len(rl)),
                res_mad=float(mad), res_rms=float(np.sqrt(np.mean(res[m]**2))))

sk = np.load('sketch_q4.npy'); fo = np.load('foto.npy')
Y = np.array([0.2126, 0.7152, 0.0722])
res = {}
# sketch: guess (1970,1280) a q4, R ~290
res['sketch_q4'] = limbe(sk[...,1], 1970, 1280, 240, 340)
# amb la luminància també
res['sketch_q4_Y'] = limbe(sk @ Y, 1970, 1280, 240, 340)
# foto: guess (3442,2232), R ~460
res['foto'] = limbe(fo[...,1], 3442, 2232, 400, 520)
res['foto_Y'] = limbe(fo @ Y, 3442, 2232, 400, 520)
for k,v in res.items(): print(k, v)
json.dump(res, open('geom.json','w'), indent=1)
