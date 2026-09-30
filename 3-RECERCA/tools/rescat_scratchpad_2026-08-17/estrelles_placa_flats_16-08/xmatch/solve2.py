import numpy as np, pandas as pd, json
from solve import load_dets, SCALE

def scan(tag, ndet, vlim, step_deg=0.15, bin_px=10.0, rng=700.0, top=8):
    dets = load_dets(tag)
    cat = pd.read_csv(f'cat_{tag}.csv')
    s = SCALE[tag]
    cat = cat[(cat.sep_deg < 4.8) & (cat.Vuse <= vlim)].reset_index(drop=True)
    U0 = cat.xi_as.values/s
    V0 = cat.eta_as.values/s
    db = dets.sort_values('snr', ascending=False).head(ndet)
    p = db.x.values - db.xc0.values
    q = db.y.values - db.yc0.values
    nb = int(2*rng/bin_px)
    recs = []
    for sigma in (+1, -1):
        Us = sigma*U0
        for th in np.arange(0, 360, step_deg):
            c, sn = np.cos(np.radians(th)), np.sin(np.radians(th))
            Ur = c*Us - sn*V0
            Vr = sn*Us + c*V0
            dx = (p[:, None] - Ur[None, :]).ravel()
            dy = (q[:, None] - Vr[None, :]).ravel()
            m = (np.abs(dx) < rng) & (np.abs(dy) < rng)
            if m.sum() < 3:
                continue
            H, _, _ = np.histogram2d(dx[m], dy[m], bins=[nb, nb],
                                     range=[[-rng, rng], [-rng, rng]])
            H2 = H[:-1, :-1]+H[1:, :-1]+H[:-1, 1:]+H[1:, 1:]
            i, j = np.unravel_index(H2.argmax(), H2.shape)
            recs.append((H2[i, j], sigma, th, -rng+(i+1)*bin_px, -rng+(j+1)*bin_px))
    recs.sort(key=lambda r: -r[0])
    print(f'--- {tag}: {len(db)} deteccions, cataleg V<={vlim} n={len(cat)} ---')
    for r in recs[:top]:
        print(f'   n={int(r[0]):3d}  paritat={r[1]:+d}  theta={r[2]:7.2f}  dx={r[3]:7.0f} dy={r[4]:7.0f}')
    # distribucio de referencia (soroll): max per angle
    allmax = np.array([r[0] for r in recs])
    print(f'   soroll: mediana del max per angle = {np.median(allmax):.1f}, p99 = {np.percentile(allmax,99):.1f}')
    return recs

if __name__ == '__main__':
    scan('r6', 24, 10.5)
    print()
    scan('sony', 38, 10.5)
    print()
    scan('sony', 38, 9.0)
    print()
    scan('sony', 20, 11.0)
