import numpy as np
from fisher import design, sigma_eps, sigma_eps_naive, L_GR

RSUN = 945.5           # arcsec, 2027-08-02
DEG  = 3600.0
RSUN_DEG = RSUN/DEG    # 0.26264 deg

# ---------- photometric anchor, taken from the 2026 Leon campaign ----------
# train B: D=89.8mm (A=63.3cm2), t=10.3 s, FWHM=5.8", sky=9.15 mag/arcsec2,
# V=5.73 -> SNR 121  (and V=9.18 -> SNR 5.0, the faintest identified: consistent)
A0, T0, FW0, MSKY0, V0, SNR0 = 63.3, 10.3, 5.8, 9.15, 5.73, 121.0
def aeff(fwhm): return 4*np.pi*(fwhm/2.3548)**2      # arcsec^2, optimal-weight area
S_over_F = 10**(-0.4*(MSKY0-V0))*aeff(FW0)
F_anchor = SNR0**2*(1+S_over_F)
K0 = F_anchor/10**(-0.4*V0)          # photons per unit 10^-0.4V for the anchor config
print(f"anchor: S/F={S_over_F:.3f}  F={F_anchor:.0f} e-  K0={K0:.4e}")

# ---------- coronal surface brightness (F+K), mag/arcsec2 ----------
_rho = np.array([1.3,1.5,2,2.5,3,4,5,6,8,10,12,15,20])
_mag = np.array([5.4,6.0,6.9,7.7,8.4,9.5,10.4,11.1,11.8,12.5,13.0,13.7,14.4])
def m_corona(rho): return np.interp(rho,_rho,_mag)

def m_bg(rho, m_sky):
    f = 10**(-0.4*m_sky) + 10**(-0.4*m_corona(rho))
    return -2.5*np.log10(f)

# ---------- star field ----------
# Tycho-2 / Gaia counts in the 2-15 Rsun annulus (47.9 sq deg), research 4:
# V<9:177  V<10:438  V<11:944  V<12:1981  V<13:4029  -> N(<V) = 944*2.09^(V-11)
SLOPE = 2.09
def n_per_sqdeg_per_mag(V):     # includes the M44 excess, averaged over the annulus
    return (944/47.9)*np.log(SLOPE)*SLOPE**(V-11)

def sample_field(hw_deg, hh_deg, rmin_rho, Vmax, rng, dx_deg=0.0, dy_deg=0.0, Vmin=3.5):
    """Monte-Carlo the stars inside a rectangular footprint (sensor centre offset
    by dx,dy deg from the Sun).  Returns x,y in arcsec from the SUN centre, and V."""
    area = 4*hw_deg*hh_deg
    Vg = np.arange(Vmin, Vmax+1e-9, 0.25)
    lam = np.array([n_per_sqdeg_per_mag(v)*0.25*area for v in Vg])
    xs=[];ys=[];Vs=[]
    for v,l in zip(Vg,lam):
        k = rng.poisson(l)
        if k==0: continue
        x = rng.uniform(-hw_deg,hw_deg,k)+dx_deg
        y = rng.uniform(-hh_deg,hh_deg,k)+dy_deg
        m = np.hypot(x,y) >= rmin_rho*RSUN_DEG
        xs.append(x[m]*DEG); ys.append(y[m]*DEG); Vs.append(np.full(m.sum(),v))
    return np.concatenate(xs),np.concatenate(ys),np.concatenate(Vs)

# ---------- per-star precision ----------
def per_star_sigma(V, rho, cfg):
    """cfg dict: area_cm2, t_s, thru (rel. to the 2026 anchor incl. extinction),
       fwhm, m_sky, floor (random systematic floor, arcsec), snr_min."""
    K = K0*(cfg['area_cm2']/A0)*(cfg['t_s']/T0)*cfg['thru']
    F = K*10**(-0.4*V)
    S = K*10**(-0.4*m_bg(rho,cfg['m_sky']))*aeff(cfg['fwhm'])
    snr = F/np.sqrt(F+S)
    k = 0.425 + 0.176*np.clip(S/(F+S),0,1)      # 0.425 source-limited -> 0.601 sky-limited
    sig_ph = k*cfg['fwhm']/snr
    sig = np.sqrt(sig_ph**2 + cfg['floor']**2)
    return snr, sig_ph, sig
