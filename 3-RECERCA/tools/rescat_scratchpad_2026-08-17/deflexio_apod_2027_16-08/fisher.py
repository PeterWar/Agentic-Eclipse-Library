import numpy as np
np.random.seed(11)
RSUN=945.6; LDEF=1.7516

# ---------- 2027 field: uniform component + M44 clump ----------
# Tycho-2 counts 2-15 Rsun (research 4):  V<9:177  V<10:438  V<11:944
# Gaia:  V<12:1981  V<13:4029     M44: 189/944 of the V<11 inside 1.5 deg of centre
CUM = {6:5,7:29,8:70,9:177,10:438,11:944,12:1981,13:4029}
def draw_field(Vlim, rin=2.0, rout=15.0):
    # magnitudes by interpolating log10 N(<V)
    Vg=np.array(sorted(CUM)); Ng=np.array([CUM[v] for v in Vg],float)
    Ntot=np.interp(Vlim,Vg,np.log10(Ng)); Ntot=10**Ntot
    n=int(round(Ntot))
    u=np.random.uniform(0,1,n)
    V=np.interp(np.log10(np.maximum(u*Ntot,1e-3)),np.log10(Ng),Vg)
    # 20% of stars belong to M44 clump at 9.63 Rsun, gaussian sigma 0.7deg=2.66 Rsun
    m44 = np.random.uniform(0,1,n) < 0.20
    th=np.random.uniform(0,2*np.pi,n)
    r=np.sqrt(np.random.uniform(rin**2,rout**2,n))
    xc,yc = 9.63*np.cos(np.radians(314.3)), 9.63*np.sin(np.radians(314.3))
    xm = xc+np.random.normal(0,2.66,n); ym = yc+np.random.normal(0,2.66,n)
    x=np.where(m44,xm,r*np.cos(th)); y=np.where(m44,ym,r*np.sin(th))
    rr=np.hypot(x,y); keep=(rr>=rin)&(rr<=rout)
    return x[keep],y[keep],V[keep]

# ---------- noise model anchored on the OBSERVER'S OWN 2026 measurements ----
# train B zero point +14.21 mag (ADU/s), gain 5.08 e-/ADU  -> V=0 gives 2.29e6 e-/s
ZP_e = 10**(14.21/2.5)*5.08          # e-/s for V=0 at Leon, X=6.02
def corona_mu(r):                    # F+K model, mag/arcsec^2 (research 4)
    rg=np.array([1.5,2,3,5,8,10,15,20]); mg=np.array([5.6,6.9,8.4,10.4,11.8,12.5,13.7,14.4])
    return np.interp(r,rg,mg)

def per_star_sigma(x,y,V,*,site,T_int,fwhm,k_ext,sky_atm,sig_sys,gain_scale=1.0):
    r=np.hypot(x,y)
    X = 6.02 if site=='leon' else 1.011
    F = ZP_e*10**(-0.4*(V + k_ext*(X-6.02)))*gain_scale   # e-/s, referenced to Leon ZP
    mu_tot = -2.5*np.log10(10**(-0.4*corona_mu(r)) + 10**(-0.4*sky_atm))
    B = ZP_e*10**(-0.4*(mu_tot + k_ext*(X-6.02)))         # e-/s/arcsec^2
    sg = fwhm/2.3548
    Aeff = 4*np.pi*sg**2                                   # arcsec^2, CRB effective area
    S=F*T_int; Nbg=B*Aeff*T_int
    snr = S/np.sqrt(np.maximum(S+Nbg,1e-9))
    k = np.where(S>Nbg,0.425,0.601)
    sig_ph = k*fwhm/np.maximum(snr,1e-6)
    return np.sqrt(sig_sys**2+sig_ph**2), snr

# ---------- Fisher: affine/quadratic/cubic plate model + epsilon ----------
def design(x,y,order,Rn):
    X=x/Rn; Y=y/Rn; cols=[np.ones_like(X)]
    for o in range(1,order+1):
        for i in range(o+1): cols.append(X**(o-i)*Y**i)
    return np.array(cols).T                       # n x m

def sigma_eps(x,y,sig,order=1,fix_scale=False,rmax_fit=None):
    r=np.hypot(x,y)
    if rmax_fit is not None:
        m=r<=rmax_fit; x,y,sig,r=x[m],y[m],sig[m],r[m]
    Rn=r.max()
    M=design(x,y,order,Rn); n,m=M.shape
    # jacobian rows: for each star, dx and dy
    # plate params: ax (m), ay (m); epsilon (1)
    dx_eps = LDEF/r*(x/r); dy_eps = LDEF/r*(y/r)          # arcsec
    if fix_scale and order==1:
        # remove isotropic scale column: keep translation + rotation + 2 shears
        # basis for linear part: [X,Y] pairs. drop the pure-scale direction.
        cols_x=[np.ones(n),np.zeros(n),M[:,1],M[:,2],np.zeros(n),np.zeros(n)]
        cols_y=[np.zeros(n),np.ones(n),np.zeros(n),np.zeros(n),M[:,1],M[:,2]]
        Jx=np.array(cols_x).T; Jy=np.array(cols_y).T
        # scale direction in this 6-space: dx=X, dy=Y  -> vector (0,0,1,0,0,1)
        v=np.zeros(6); v[2]=1; v[5]=1; v/=np.linalg.norm(v)
        P=np.eye(6)-np.outer(v,v)
        Jx=Jx@P; Jy=Jy@P
    else:
        Z=np.zeros((n,m))
        Jx=np.hstack([M,Z]); Jy=np.hstack([Z,M])
    Jx=np.hstack([Jx,dx_eps[:,None]]); Jy=np.hstack([Jy,dy_eps[:,None]])
    W=1.0/sig**2
    F=(Jx*W[:,None]).T@Jx + (Jy*W[:,None]).T@Jy
    C=np.linalg.pinv(F,rcond=1e-12)
    return np.sqrt(C[-1,-1]), len(x)

print("="*78); print("VALIDATION AGAINST THE 2026 CAMPAIGN"); print("="*78)
for lab,N,rin,rout,sper,exp in [("train A",38,2.16,13.7,1.61,1.39),("train B",22,2.16,9.5,0.64,0.57)]:
    v=[]
    for _ in range(400):
        r=np.sqrt(np.random.uniform(rin**2,rout**2,N)); th=np.random.uniform(0,2*np.pi,N)
        s,_=sigma_eps(r*np.cos(th),r*np.sin(th),np.full(N,sper),order=1)
        v.append(s)
    print(f"  {lab}: predicted sigma(eps)={np.mean(v):.3f}  reported {exp}")
print(f"  combined predicted {1/np.sqrt(1/np.mean(1.39)**2):.2f} -> quadrature of the two above")

print()
print("="*78); print("2027 FORECAST  (Luxor, alt 81.7, T_int on the eclipse field)"); print("="*78)
scen = [
 ("2026 gear flown unchanged",      13.7, 5.0, 0.50, 12.0, 263, 1),
 ("+ r' filter, mono-equiv, Gaia",  13.7, 3.5, 0.15, 12.0, 263, 1),
 ("+ 3rd-order plate model",        13.7, 3.5, 0.15, 12.0, 263, 3),
 ("Bruns-class technique",          13.7, 2.8, 0.06, 12.0, 263, 3),
]
for lab,rout,fwhm,ssys,skyatm,T,order in scen:
    x,y,V=draw_field(12.0,2.0,rout)
    sig,snr=per_star_sigma(x,y,V,site='luxor',T_int=T,fwhm=fwhm,k_ext=0.20,
                           sky_atm=skyatm,sig_sys=ssys)
    m=snr>=7
    s1,N1=sigma_eps(x[m],y[m],sig[m],order=order)
    s2,_ =sigma_eps(x[m],y[m],sig[m],order=order,fix_scale=(order==1))
    print(f"{lab:34s} N={N1:4d}  FWHM={fwhm:.1f}\"  sys={ssys:.2f}\"  order={order}"
          f"  sigma(eps)={s1:.4f}")
