"""Self-contained error-budget core for the 2027 eclipse deflection experiment."""
import numpy as np

L_GR   = 1.7516      # arcsec deflection at 1 Rsun (GR); Newton = 0.8758
RSUN27 = 945.5       # arcsec, 2027-08-02
RSUN26 = 950.0
DEG    = 3600.0

# ------------------------------------------------------------------ Fisher
def design(x, y, order=1, rsun=RSUN27):
    """(2N x P) design matrix; last column is the deflection template."""
    n = len(x); r = np.hypot(x, y); rho = r/rsun
    ux, uy = x/r, y/r
    xs, ys = x/r.max(), y/r.max()          # normalised, for conditioning
    cols = [(np.ones(n), np.zeros(n)),     # translation x
            (np.zeros(n), np.ones(n)),     # translation y
            (-ys, xs),                     # rotation
            (xs, ys)]                      # isotropic scale
    if order >= 2:
        cols += [(xs, -ys), (ys, xs)]      # the two shears -> full affine
        for (p, q) in [(2,0),(1,1),(0,2)]:
            t = xs**p * ys**q
            cols += [(t, np.zeros(n)), (np.zeros(n), t)]
    if order >= 3:
        for (p, q) in [(3,0),(2,1),(1,2),(0,3)]:
            t = xs**p * ys**q
            cols += [(t, np.zeros(n)), (np.zeros(n), t)]
    cols.append((L_GR*ux/rho, L_GR*uy/rho))
    A = np.zeros((2*n, len(cols)))
    for j,(cx,cy) in enumerate(cols):
        A[0::2, j] = cx; A[1::2, j] = cy
    return A

def fit_cov(x, y, sig, order=1, rsun=RSUN27, fix_scale=False):
    A = design(x, y, order, rsun)
    if fix_scale:
        A = np.delete(A, 3, axis=1)
    sig = np.atleast_1d(sig)
    if sig.size == 1: sig = np.full(len(x), sig[0])
    w = np.repeat(1.0/sig**2, 2)
    F = A.T @ (A*w[:,None])
    return np.linalg.inv(F), A, w

def sigma_eps(x, y, sig, order=1, rsun=RSUN27, fix_scale=False):
    C,_,_ = fit_cov(x, y, sig, order, rsun, fix_scale)
    return np.sqrt(C[-1,-1])

def sigma_eps_naive(x, y, sig, rsun=RSUN27):
    """No plate model: the pure Freundlich-Ledermann statistic."""
    rho = np.hypot(x,y)/rsun
    sig = np.atleast_1d(sig)
    if sig.size == 1: sig = np.full(len(rho), sig[0])
    return 1.0/np.sqrt(np.sum((L_GR/rho)**2/sig**2))

def bias_eps(x, y, sig, dfield, order=1, rsun=RSUN27, fix_scale=False):
    """Bias induced in eps by a coherent displacement field dfield=(dx,dy) [arcsec]."""
    C, A, w = fit_cov(x, y, sig, order, rsun, fix_scale)
    d = np.empty(2*len(x)); d[0::2] = dfield[0]; d[1::2] = dfield[1]
    return (C @ (A.T @ (w*d)))[-1]

# ------------------------------------------------------- 2027 star field
CUM = {6:5, 7:29, 8:70, 9:177, 10:438, 11:944, 12:1981, 13:4029}  # 2-15 Rsun, 47.9 sq.deg
_Vg = np.array(sorted(CUM), float)
_Ng = np.log10([CUM[v] for v in sorted(CUM)])
ANNULUS_AREA = 47.9

def cum_density(V):
    """Stars per square degree brighter than V, averaged over the 2-15 Rsun annulus."""
    return 10**np.interp(V, _Vg, _Ng)/ANNULUS_AREA

def sample_rect(hw_deg, hh_deg, Vlim, rng, rmin_rho=1.9, dx_deg=0.0, dy_deg=0.0, Vmin=4.0):
    """Stars inside a rectangular sensor footprint whose centre is offset (dx,dy)
    degrees from the Sun.  Returns x,y (arcsec from the SUN) and V."""
    area = 4*hw_deg*hh_deg
    edges = np.arange(Vmin, Vlim+1e-9, 0.5)
    xs=[]; ys=[]; Vs=[]
    for lo in edges:
        hi = min(lo+0.5, Vlim)
        if hi <= lo: continue
        lam = (cum_density(hi)-cum_density(lo))*area
        k = rng.poisson(lam)
        if k == 0: continue
        X = rng.uniform(-hw_deg,hw_deg,k)+dx_deg
        Y = rng.uniform(-hh_deg,hh_deg,k)+dy_deg
        keep = np.hypot(X,Y) >= rmin_rho*RSUN27/DEG
        xs.append(X[keep]*DEG); ys.append(Y[keep]*DEG)
        Vs.append(rng.uniform(lo,hi,k)[keep])
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(Vs)

# ------------------------------------------------------- photometry
A0, T0, FW0, MSKY0, V0, SNR0 = 63.3, 10.3, 5.8, 9.15, 5.73, 121.0   # 2026 train-B anchor
def aeff(fwhm): return 4*np.pi*(fwhm/2.3548)**2
_SF = 10**(-0.4*(MSKY0-V0))*aeff(FW0)
K_ANCHOR = SNR0**2*(1+_SF)/10**(-0.4*V0)

_rc = np.array([1.3,1.5,2,2.5,3,4,5,6,8,10,12,15,20])
_mc = np.array([5.4,6.0,6.9,7.7,8.4,9.5,10.4,11.1,11.8,12.5,13.0,13.7,14.4])
def m_corona(rho): return np.interp(rho,_rc,_mc)
def m_bg(rho, m_sky):
    return -2.5*np.log10(10**(-0.4*m_sky)+10**(-0.4*m_corona(rho)))

def star_sigma(V, rho, area_cm2, t_s, thru, fwhm, m_sky):
    """Returns SNR and the PHOTON-limited centroid sigma per coordinate (arcsec)."""
    K = K_ANCHOR*(area_cm2/A0)*(t_s/T0)*thru
    F = K*10**(-0.4*V)
    S = K*10**(-0.4*m_bg(rho,m_sky))*aeff(fwhm)
    snr = F/np.sqrt(F+S)
    k = 0.425 + 0.176*(S/(F+S))          # 0.425 source-limited .. 0.601 sky-limited
    return snr, k*fwhm/snr
