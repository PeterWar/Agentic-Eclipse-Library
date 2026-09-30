"""Leakage of correlated radial patterns into the deflection amplitude."""
import numpy as np, sys
sys.path.insert(0, '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/604fa71e-4fd9-4d66-a0e5-157c6621ceb3/scratchpad')
from model import *

def leak(xi, eta_, sig, pattern, order=1, fix_scale=False, rmin=1.8):
    """Bias in eps induced by an unmodelled RADIAL displacement field
    pattern(rho_deg) [arcsec], via the generalised least squares estimator.
    Returns d(eps)/d(amplitude)."""
    rho = np.hypot(xi, eta_)
    m = (rho > rmin * RSUN_DEG) & np.isfinite(sig) & (sig > 0)
    xi, eta_, sig, rho = xi[m], eta_[m], sig[m], rho[m]
    N = len(xi)
    cols_x, cols_y = [], []
    cols_x.append(np.ones(N));  cols_y.append(np.zeros(N))
    cols_x.append(np.zeros(N)); cols_y.append(np.ones(N))
    if not fix_scale:
        cols_x.append(xi); cols_y.append(eta_)
    cols_x.append(-eta_); cols_y.append(xi)
    cols_x.append(xi);    cols_y.append(-eta_)
    cols_x.append(eta_);  cols_y.append(xi)
    if order >= 2:
        P = basis(xi, eta_, order)[:, 3:]
        for j in range(P.shape[1]):
            cols_x.append(P[:, j]); cols_y.append(np.zeros(N))
        for j in range(P.shape[1]):
            cols_x.append(np.zeros(N)); cols_y.append(P[:, j])
    d = L_GR * RSUN_ARCSEC / (rho * 3600.0)
    ux, uy = xi / rho, eta_ / rho
    cols_x.append(d * ux); cols_y.append(d * uy)
    A = np.vstack([np.array(cols_x).T, np.array(cols_y).T])
    w = 1.0 / np.concatenate([sig, sig]) ** 2
    F = A.T @ (A * w[:, None]); C = np.linalg.inv(F)
    disp = pattern(rho)                       # arcsec, radial, unit amplitude
    z = np.concatenate([disp * ux, disp * uy])
    beta = C @ (A.T @ (z * w))
    return beta[-1]

xi, eta_, V = make_field(seed=3)

# use the recommended config's per-star sigma for the weighting
sig_all = np.full(len(V), 0.12)

print("LEAKAGE of a radial distortion of amplitude 1 arcsec AT THE FIELD EDGE")
print("(i.e. d eps / d A_edge). Multiply by the residual you actually have.\n")
fields = [('VSD90SS + FF, 4.18x2.78 deg (half-diag 2.51)', 4.18, 2.78),
          ('VSD90SS + APS-C, 2.73x1.82 (half-diag 1.64)',  2.73, 1.82),
          ('VSD90SS+0.79x + FF, 5.29x3.53 (half-diag 3.18)',5.29, 3.53),
          ('Sony 300 + FF, 6.88x4.58 (half-diag 4.13)',    6.88, 4.58),
          ('Bruns NP101is, 1.9x1.4 (half-diag 1.18)',      1.90, 1.40)]
print(f"{'field':50s} {'pattern':>8s} {'1st':>9s} {'3rd':>9s} {'5th':>9s}")
print('-'*92)
for nm, w, h in fields:
    inx = (np.abs(xi) < w/2) & (np.abs(eta_) < h/2)
    x, y, s = xi[inx], eta_[inx], sig_all[inx]
    Redge = np.hypot(w, h)/2
    for pname, n in (('r^2', 2), ('r^3', 3), ('r^5', 5)):
        pat = lambda rho, n=n, R=Redge: (rho/R)**n
        vals = []
        for order in (1, 3, 5):
            try:
                vals.append(leak(x, y, s, pat, order=order))
            except Exception:
                vals.append(np.nan)
        print(f"{nm if n==2 else '':50s} {pname:>8s} {vals[0]:9.4f} {vals[1]:9.4f} {vals[2]:9.4f}")
    print()

print("\nLEAKAGE of a fractional PLATE-SCALE error dS/S = 1e-6  ->  d eps")
print(f"{'field':50s} {'linear fit':>12s} {'scale fixed externally':>24s}")
print('-'*90)
for nm, w, h in fields:
    inx = (np.abs(xi) < w/2) & (np.abs(eta_) < h/2)
    x, y, s = xi[inx], eta_[inx], sig_all[inx]
    pat = lambda rho: 1e-6 * rho * 3600.0     # radial displacement, arcsec
    a = leak(x, y, s, pat, order=1, fix_scale=False)
    b = leak(x, y, s, pat, order=1, fix_scale=True)
    print(f"{nm:50s} {a:12.6f} {b:24.6f}")
