"""Compara els tres marcs de projeccio i deixa la solucio bona."""
import numpy as np, pandas as pd, json
from solve import load_dets, SCALE
from refine import fit_affine, fit_similarity, predict, COARSE

FRAMES = {'eq_norefr': ('xi_as', 'eta_as'),
          'hor_refr':  ('xh_as', 'yh_as'),
          'hor_norefr': ('xh0_as', 'yh0_as')}


def match_and_fit(tag, cx, cy, vlim=11.0, tol0=45., tolmin=7.0, nit=8, model='affine'):
    dets = load_dets(tag)
    cat = pd.read_csv(f'cat2_{tag}.csv')
    cat = cat[(cat.sep_deg < 5.0) & (cat.Vuse <= vlim)].reset_index(drop=True)
    s = SCALE[tag]
    c = COARSE[tag]
    th = np.radians(c['theta']); sg = c['sigma']
    par = np.array([dets.xc0[0]+c['dx'], np.cos(th)*sg/s, -np.sin(th)/s,
                    dets.yc0[0]+c['dy'], np.sin(th)*sg/s, np.cos(th)/s])
    xi = cat[cx].values; eta = cat[cy].values
    X = dets.x.values; Y = dets.y.values
    for tol in np.geomspace(tol0, tolmin, nit):
        px, py = predict(par, xi, eta)
        D = np.hypot(X[:, None]-px[None, :], Y[:, None]-py[None, :])
        j = D.argmin(axis=1); dmin = D[np.arange(len(X)), j]
        ok = dmin < tol
        for jj in np.unique(j[ok]):
            w = np.where(ok & (j == jj))[0]
            if len(w) > 1:
                k = w[np.argmin(dmin[w])]; ok[w] = False; ok[k] = True
        if ok.sum() < 4:
            break
        if model == 'affine':
            par = fit_affine(xi[j[ok]], eta[j[ok]], X[ok], Y[ok])
        else:
            par, _, _ = fit_similarity(xi[j[ok]], eta[j[ok]], X[ok], Y[ok])
    px, py = predict(par, xi[j[ok]], eta[j[ok]])
    rms = np.sqrt(((X[ok]-px)**2 + (Y[ok]-py)**2).mean())
    x0, a, b, y0, cc, d = par
    sx = 1/np.hypot(a, cc); sy = 1/np.hypot(b, d)
    skew = np.degrees(np.arccos(abs((a*b+cc*d)/(np.hypot(a, cc)*np.hypot(b, d))))) - 90.
    return dict(n=int(ok.sum()), rms=float(rms), sx=float(sx), sy=float(sy),
                skew=float(skew), par=par, ok=ok, j=j, dets=dets, cat=cat)


for tag in ('sony', 'r6'):
    print(f'===== {tag}  (escala mesurada de referencia: {SCALE[tag]} "/px) =====')
    for name, (cx, cy) in FRAMES.items():
        r = match_and_fit(tag, cx, cy)
        print(f'  {name:11s} afi : n={r["n"]:3d} rms={r["rms"]:5.2f} px  '
              f'escala1={r["sx"]:.4f} escala2={r["sy"]:.4f} '
              f'anisotropia={100*(r["sx"]/r["sy"]-1):+.3f}%  no-perp={r["skew"]:+.3f} deg')
    for name, (cx, cy) in FRAMES.items():
        r = match_and_fit(tag, cx, cy, model='sim')
        print(f'  {name:11s} sim : n={r["n"]:3d} rms={r["rms"]:5.2f} px  escala={r["sx"]:.4f}')
    print()
