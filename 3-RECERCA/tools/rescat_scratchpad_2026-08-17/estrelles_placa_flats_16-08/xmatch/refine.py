"""Refinament iteratiu: aparellament + ajust afi per minims quadrats."""
import numpy as np, pandas as pd, json
from solve import load_dets, SCALE

COARSE = {'sony': dict(sigma=+1, theta=268.35, dx=-20., dy=-10.),
          'r6':   dict(sigma=+1, theta=235.20, dx=-10., dy=0.)}


def predict(par, xi, eta):
    """par = [x0, a, b, y0, c, d]; retorna x, y al sensor."""
    x = par[0] + par[1]*xi + par[2]*eta
    y = par[3] + par[4]*xi + par[5]*eta
    return x, y


def fit_affine(xi, eta, x, y):
    A = np.column_stack([np.ones_like(xi), xi, eta])
    px, *_ = np.linalg.lstsq(A, x, rcond=None)
    py, *_ = np.linalg.lstsq(A, y, rcond=None)
    return np.concatenate([px, py])


def fit_similarity(xi, eta, x, y):
    """x = x0 + a*xi + b*eta ; y = y0 + c*xi + d*eta amb (a,b,c,d) similitud
    (d = s*a/|..|) -> 4 parametres: x0, y0, k, m amb [a b; c d] = [k -m; m k]
    (paritat +1) o [k m; m -k] (paritat -1)."""
    n = len(xi)
    best = None
    for par in (+1, -1):
        if par > 0:
            # x = x0 + k*xi - m*eta ; y = y0 + m*xi + k*eta
            A = np.zeros((2*n, 4))
            A[:n, 0] = 1; A[:n, 2] = xi;  A[:n, 3] = -eta
            A[n:, 1] = 1; A[n:, 2] = eta; A[n:, 3] = xi
        else:
            # x = x0 + k*xi + m*eta ; y = y0 + m*xi - k*eta
            A = np.zeros((2*n, 4))
            A[:n, 0] = 1; A[:n, 2] = xi;  A[:n, 3] = eta
            A[n:, 1] = 1; A[n:, 2] = eta; A[n:, 3] = -xi
        b = np.concatenate([x, y])
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
        res = b - A@sol
        rms = np.sqrt((res**2).sum()/n)
        x0, y0, k, m = sol
        if par > 0:
            p6 = np.array([x0, k, -m, y0, m, k])
        else:
            p6 = np.array([x0, k, m, y0, m, -k])
        if best is None or rms < best[0]:
            best = (rms, p6, par)
    return best[1], best[2], best[0]


def run(tag, tol0=40.0, tolmin=6.0, vlim=11.0, model='sim', verbose=True):
    dets = load_dets(tag)
    cat = pd.read_csv(f'cat_{tag}.csv')
    cat = cat[(cat.sep_deg < 5.0) & (cat.Vuse <= vlim)].reset_index(drop=True)
    s = SCALE[tag]
    c = COARSE[tag]
    th = np.radians(c['theta']); sg = c['sigma']
    a = np.cos(th)*sg/s; b = -np.sin(th)/s
    cc = np.sin(th)*sg/s; d = np.cos(th)/s
    par = np.array([dets.xc0[0]+c['dx'], a, b, dets.yc0[0]+c['dy'], cc, d])

    xi = cat.xi_as.values; eta = cat.eta_as.values
    dx_ = dets.x.values; dy_ = dets.y.values
    pairs = None
    for it, tol in enumerate(np.geomspace(tol0, tolmin, 7)):
        px, py = predict(par, xi, eta)
        D = np.hypot(dx_[:, None]-px[None, :], dy_[:, None]-py[None, :])
        j = D.argmin(axis=1)
        dmin = D[np.arange(len(dx_)), j]
        ok = dmin < tol
        # unicitat: si dues deteccions volen la mateixa estrella, guanya la mes propera
        for jj in np.unique(j[ok]):
            w = np.where(ok & (j == jj))[0]
            if len(w) > 1:
                keep = w[np.argmin(dmin[w])]
                ok[w] = False; ok[keep] = True
        pairs = (np.where(ok)[0], j[ok])
        if ok.sum() < 3:
            break
        if model == 'sim':
            par, parity, rms = fit_similarity(xi[j[ok]], eta[j[ok]], dx_[ok], dy_[ok])
        else:
            par = fit_affine(xi[j[ok]], eta[j[ok]], dx_[ok], dy_[ok])
            parity = np.sign(par[1]*par[5]-par[2]*par[4])
            px2, py2 = predict(par, xi[j[ok]], eta[j[ok]])
            rms = np.sqrt(((dx_[ok]-px2)**2 + (dy_[ok]-py2)**2).mean())
        if verbose:
            print(f'  it{it} tol={tol:5.1f} px  n={ok.sum():3d}  rms={rms:5.2f} px')
    return dets, cat, par, pairs, rms


def decompose(par, tag):
    x0, a, b, y0, c, d = par
    M = np.array([[a, b], [c, d]])
    det = np.linalg.det(M)
    # escala: arcsec per pixel = 1/|columna|
    sx = 1.0/np.hypot(a, c)      # arcsec/px al llarg de xi
    sy = 1.0/np.hypot(b, d)
    scale = 1.0/np.sqrt(abs(det))
    # direccio del NORD (eta creixent) al sensor
    nx, ny = b, d
    # angle mesurat des de "amunt" a la imatge (-y) cap a l'esquerra?  Definim:
    # PA_nord = angle antihorari des de la vertical amunt de la imatge (-y) cap a +x
    pa_north = np.degrees(np.arctan2(nx, -ny)) % 360
    ex, ey = a, c
    pa_east = np.degrees(np.arctan2(ex, -ey)) % 360
    return dict(scale=scale, sx=sx, sy=sy, det=det, mirror=bool(det > 0),
                pa_north=pa_north, pa_east=pa_east, x0=x0, y0=y0,
                nonperp=float(np.degrees(np.arccos(abs(
                    (a*b+c*d)/(np.hypot(a, c)*np.hypot(b, d))))) - 90.0))


if __name__ == '__main__':
    out = {}
    for tag in ('sony', 'r6'):
        print(f'=== {tag} (similitud) ===')
        dets, cat, par, pairs, rms = run(tag, model='sim')
        g = decompose(par, tag)
        print(f'  escala={g["scale"]:.4f} "/px   PA nord={g["pa_north"]:.3f} deg  '
              f'PA est={g["pa_east"]:.3f}  mirall={g["mirror"]}  rms={rms:.2f}')
        print(f'=== {tag} (afi) ===')
        dets2, cat2, par2, pairs2, rms2 = run(tag, model='affine', verbose=False)
        g2 = decompose(par2, tag)
        print(f'  n={len(pairs2[0])} escala_xi={g2["sx"]:.4f} escala_eta={g2["sy"]:.4f} '
              f'PA nord={g2["pa_north"]:.3f}  no-perp={g2["nonperp"]:+.3f} deg  rms={rms2:.2f}')
        i, j = pairs
        rec = []
        px, py = predict(par, cat.xi_as.values, cat.eta_as.values)
        for ii, jj in zip(i, j):
            rec.append(dict(det=dets.id[ii], x=dets.x[ii], y=dets.y[ii],
                            HIP=cat.HIP[jj], TYC=cat.TYC[jj], HD=cat.HD[jj],
                            V=cat.Vuse[jj], BV=cat.BVuse[jj], Sp=cat.Sp[jj],
                            sep_deg=cat.sep_deg[jj],
                            dx=dets.x[ii]-px[jj], dy=dets.y[ii]-py[jj],
                            resid=np.hypot(dets.x[ii]-px[jj], dets.y[ii]-py[jj]),
                            flux=dets.flux[ii], snr=dets.snr[ii]))
        pd.DataFrame(rec).to_csv(f'match_{tag}.csv', index=False)
        np.save(f'par_{tag}.npy', par)
        out[tag] = dict(par=list(par), rms=float(rms), n=int(len(i)), **{k: (float(v) if not isinstance(v, bool) else v) for k, v in g.items()})
        print()
    json.dump(out, open('solution.json', 'w'), indent=1)
