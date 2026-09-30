"""
Instrument optimisation for the 2027-08-02 eclipse gravitational deflection measurement.
Fisher-matrix model, anchored on the 2026 Leon campaign's measured performance.
"""
import numpy as np

RSUN_ARCSEC = 945.5          # solar semidiameter 2027-08-02 (Skyfield/DE440s, research 4)
RSUN_DEG = RSUN_ARCSEC / 3600.0
L_GR = 1.7516                # arcsec at 1 Rsun

# ---------------------------------------------------------------- star field
# Tycho-2 / Gaia counts in the 2-15 Rsun annulus (47.9 deg^2), research 4
_V = np.array([6., 7., 8., 9., 10., 11., 12., 13.])
_N = np.array([5., 29., 70., 177., 438., 944., 1981., 4029.])
# M44 members inside the annulus (Gaia DR3 selection, research 4)
_VM = np.array([9., 10., 11., 13.])
_NM = np.array([40., 77., 123., 218.])
ANNULUS_DEG2 = 47.9

def cum_all(V):
    """Cumulative star count brighter than V in the 2-15 Rsun annulus."""
    lg = np.interp(V, _V, np.log10(_N),
                   left=np.log10(_N[0]) + 0.40 * (V - _V[0]) if np.isscalar(V) else None)
    lg = np.where(V < 6, np.log10(_N[0]) + 0.40 * (V - 6), lg)
    lg = np.where(V > 13, np.log10(_N[-1]) + 0.30 * (V - 13), lg)
    return 10 ** lg

def cum_m44(V):
    lg = np.interp(V, _VM, np.log10(_NM))
    lg = np.where(V < 9, np.log10(_NM[0]) + 0.40 * (V - 9), lg)
    lg = np.where(V > 13, np.log10(_NM[-1]) + 0.30 * (V - 13), lg)
    return 10 ** lg

def make_field(seed=1, Vmax=14.5, rmax_rsun=30.0):
    """Monte-Carlo realisation of the 2027 field: smooth component + M44 clump.
    Returns xi, eta (deg, tangent plane, Sun at origin), V."""
    rng = np.random.default_rng(seed)
    Vgrid = np.arange(4.0, Vmax + 0.001, 0.25)
    # smooth surface density (per deg^2) from the annulus counts minus M44
    n_smooth = (cum_all(Vgrid) - cum_m44(Vgrid)) / ANNULUS_DEG2
    n_m44 = cum_m44(Vgrid)

    # smooth stars over a disc of rmax, with a hole at r < 1.2 Rsun (Moon)
    rmax = rmax_rsun * RSUN_DEG
    rmin = 1.2 * RSUN_DEG
    area = np.pi * (rmax**2 - rmin**2)
    Ns = int(round(n_smooth[-1] * area))
    u = rng.uniform(0, 1, Ns)
    r = np.sqrt(rmin**2 + u * (rmax**2 - rmin**2))
    th = rng.uniform(0, 2 * np.pi, Ns)
    xs, ys = r * np.cos(th), r * np.sin(th)
    # sample V from the differential LF
    cdf = n_smooth / n_smooth[-1]
    Vs = np.interp(rng.uniform(0, 1, Ns), cdf, Vgrid)

    # M44: uniform disc radius 1.0 deg centred 2.530 deg from Sun at PA 314.3
    pa = np.deg2rad(314.3)
    cx, cy = 2.530 * np.sin(pa), 2.530 * np.cos(pa)   # x=east, y=north
    Nm = int(round(n_m44[-1]))
    rr = 1.0 * np.sqrt(rng.uniform(0, 1, Nm))
    tt = rng.uniform(0, 2 * np.pi, Nm)
    xm, ym = cx + rr * np.cos(tt), cy + rr * np.sin(tt)
    cdfm = n_m44 / n_m44[-1]
    Vm = np.interp(rng.uniform(0, 1, Nm), cdfm, Vgrid)

    xi = np.concatenate([xs, xm]); eta = np.concatenate([ys, ym]); V = np.concatenate([Vs, Vm])
    return xi, eta, V

# ---------------------------------------------------------------- background
# Coronal F+K surface brightness, mag/arcsec^2 (research 4)
_CR = np.array([1.8, 2., 3., 5., 8., 10., 15., 25.])
_CB = np.array([6.51, 6.9, 8.4, 10.4, 11.8, 12.5, 13.7, 15.0])

def mu_bg(r_rsun, mu_scattered):
    """Combined coronal + atmospheric-scattered background, mag/arcsec^2."""
    mu_c = np.interp(np.log10(np.clip(r_rsun, 1.5, 30)), np.log10(_CR), _CB)
    f = 10 ** (-0.4 * mu_c) + 10 ** (-0.4 * mu_scattered)
    return -2.5 * np.log10(f)

# ---------------------------------------------------------------- photometry
# Anchor: 2026 train B. V=5.73 -> SNR 121 in one 10.3 s frame.
A_2026 = np.pi * (8.98 / 2) ** 2          # cm^2, 494/5.5 = 89.8 mm
T_2026 = 10.3
FWHM_2026 = 5.8
MU_2026 = 9.15
AEXT_2026 = 2.00                          # mag, X=6.03, dusty low Sun
ETA_BAYER = 1.00                          # reference system efficiency x band
ETA_MONO_R = 1.33                         # mono + Sloan r' vs Bayer luminance
ETA_MONO_L = 2.80                         # mono unfiltered
ETA_MONO_NB = 0.28                        # mono + 30 nm narrowband

def _calib():
    om = 4 * np.pi * (FWHM_2026 / 2.355) ** 2
    # S = K*10^-0.4(V+A)*A*t*eta ; B = K*10^-0.4 mu * om*A*t*eta
    # SNR = S/sqrt(S+B) = 121  -> solve for K
    rs = 10 ** (-0.4 * (5.73 + AEXT_2026)) * A_2026 * T_2026
    rb = 10 ** (-0.4 * MU_2026) * om * A_2026 * T_2026
    # 121 = K*rs/sqrt(K*(rs+rb))  -> K = 121^2 * (rs+rb)/rs^2
    return 121.0 ** 2 * (rs + rb) / rs ** 2

KPH = _calib()

def snr(V, mu, D_mm, t_tot, fwhm, eta, aext):
    om = 4 * np.pi * (fwhm / 2.355) ** 2
    A = np.pi * (D_mm / 20.0) ** 2
    S = KPH * 10 ** (-0.4 * (V + aext)) * A * t_tot * eta
    B = KPH * 10 ** (-0.4 * mu) * om * A * t_tot * eta
    return S / np.sqrt(S + B)

# ---------------------------------------------------------------- Fisher
def basis(xi, eta, order):
    cols = []
    for n in range(order + 1):
        for i in range(n + 1):
            cols.append(xi ** (n - i) * eta ** i)
    return np.array(cols).T          # (N, K)

def sigma_eps(xi, eta, sig, order=1, fix_scale=False, rmin=1.8, rmax=None,
              return_cov=False):
    """xi,eta in deg (tangent plane, Sun at origin); sig = per-star 1-sigma
    per coordinate, arcsec.  Plate model is parameterised as
        translation(2) + isotropic scale(1) + rotation(1) + 2 shears
        + free per-axis polynomial terms of order 2..`order`.
    fix_scale=True deletes ONLY the isotropic-scale direction (i.e. the plate
    scale has been measured externally, Bruns-style)."""
    rho = np.hypot(xi, eta)
    m = rho > rmin * RSUN_DEG
    if rmax is not None:
        m &= rho < rmax * RSUN_DEG
    m &= np.isfinite(sig) & (sig > 0)
    xi, eta, sig, rho = xi[m], eta[m], sig[m], rho[m]
    N = len(xi)
    nhigh = ((order + 1) * (order + 2) // 2) - 3 if order >= 2 else 0
    npar_needed = 6 + 2 * nhigh + 1
    if 2 * N < npar_needed + 8:
        return (np.nan, N) if not return_cov else (np.nan, N, None)

    cols_x, cols_y = [], []
    cols_x.append(np.ones(N));  cols_y.append(np.zeros(N))    # tx
    cols_x.append(np.zeros(N)); cols_y.append(np.ones(N))     # ty
    if not fix_scale:
        cols_x.append(xi);      cols_y.append(eta)            # isotropic scale
    cols_x.append(-eta);        cols_y.append(xi)             # rotation
    cols_x.append(xi);          cols_y.append(-eta)           # shear 1
    cols_x.append(eta);         cols_y.append(xi)             # shear 2
    if order >= 2:
        P = basis(xi, eta, order)[:, 3:]                      # monomials deg>=2
        for j in range(P.shape[1]):
            cols_x.append(P[:, j]); cols_y.append(np.zeros(N))
        for j in range(P.shape[1]):
            cols_x.append(np.zeros(N)); cols_y.append(P[:, j])
    d = L_GR * RSUN_ARCSEC / (rho * 3600.0)   # arcsec of deflection at eps=1
    cols_x.append(d * xi / rho); cols_y.append(d * eta / rho)

    Ax = np.array(cols_x).T; Ay = np.array(cols_y).T
    A = np.vstack([Ax, Ay])
    w = 1.0 / np.concatenate([sig, sig]) ** 2
    F = A.T @ (A * w[:, None])
    try:
        C = np.linalg.inv(F)
    except np.linalg.LinAlgError:
        return (np.nan, N) if not return_cov else (np.nan, N, None)
    s = np.sqrt(abs(C[-1, -1]))
    return (s, N) if not return_cov else (s, N, C)
