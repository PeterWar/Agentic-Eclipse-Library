import numpy as np
rng=np.random.default_rng(7)
L=1.7516

def sigma_eps(xy, sig_star, model="linear6", weights=None):
    """xy: star positions in units of solar radii, Sun at origin.
       Returns sigma(epsilon) marginalising over the plate model."""
    x,y=xy[:,0],xy[:,1]; r=np.hypot(x,y)
    n=len(r)
    if weights is None: w=np.ones(n)/sig_star**2
    else: w=weights
    # deflection partials (arcsec) per unit epsilon, radial outward
    dxi = L*(x/r)/r ; deta = L*(y/r)/r
    cols=[]
    if model=="linear6":
        # dxi = a0 + a1 x + a2 y ; deta = b0 + b1 x + b2 y   (6 params, includes scale/rot/shear)
        base=[(np.ones(n),0),(x,0),(y,0),(np.ones(n),1),(x,1),(y,1)]
    elif model=="scale_only":
        base=[(np.ones(n),0),(np.ones(n),1),(x,0),(y,1)]   # translation + isotropic scale
    elif model=="linear6+cubic":
        r2=x*x+y*y
        base=[(np.ones(n),0),(x,0),(y,0),(np.ones(n),1),(x,1),(y,1)]
        for p in (x*x, x*y, y*y, x*r2, y*r2, x*x*x, y*y*y):
            base.append((p,0)); base.append((p,1))
    # build design matrix stacked over both coords
    N=2*n
    A=np.zeros((N,1+len(base)))
    A[:n,0]=dxi; A[n:,0]=deta
    for j,(v,ax) in enumerate(base):
        if ax==0: A[:n,1+j]=v
        else:     A[n:,1+j]=v
    W=np.concatenate([w,w])
    F=A.T@(A*W[:,None])
    C=np.linalg.pinv(F)
    return np.sqrt(C[0,0])

def sample_field(n, rmin, rmax, halfw, halfh, seed):
    rr=np.random.default_rng(seed); out=[]
    while len(out)<n:
        x=rr.uniform(-halfw,halfw); y=rr.uniform(-halfh,halfh)
        r=np.hypot(x,y)
        if rmin<=r<=rmax: out.append((x,y))
    return np.array(out)

print("=== A. REPRODUCE THE 2026 RESULT ===")
# train A: 38 stars, field 7.14x4.77 deg, Rsun=15.8' -> half-widths in Rsun
Rs=15.8/60.
A_hw,A_hh=3.57/Rs,2.385/Rs ; B_hw,B_hh=2.085/Rs,1.39/Rs
for name,n,hw,hh,sig in [("Train A",38,A_hw,A_hh,1.61),("Train B",22,B_hw,B_hh,0.64)]:
    vals=[sigma_eps(sample_field(n,2.16,min(np.hypot(hw,hh),13.7),hw,hh,s),sig) for s in range(200)]
    print(f"  {name}: sigma(eps) = {np.median(vals):.2f}  (campaign reported "
          f"{'1.39' if name=='Train A' else '0.57'})   [free 6-par plate]")
# combined
vals=[]
for s in range(200):
    a=sample_field(38,2.16,16.,A_hw,A_hh,s); b=sample_field(22,2.16,9.5,B_hw,B_hh,s+999)
    # combine as independent -> quadrature of inverse variances
    va=sigma_eps(a,1.61); vb=sigma_eps(b,0.64)
    vals.append(1/np.sqrt(1/va**2+1/vb**2))
print(f"  Combined: sigma(eps) = {np.median(vals):.2f}   (campaign reported 0.53)")

print("\n=== B. DEGENERACY COST of solving plate scale from the eclipse frame itself ===")
for name,n,hw,hh in [("Train A",38,A_hw,A_hh),("Train B",22,B_hw,B_hh)]:
    f=[];
    for s in range(200):
        xy=sample_field(n,2.16,min(np.hypot(hw,hh),13.7),hw,hh,s)
        free=sigma_eps(xy,1.0,"linear6")
        # scale externally known: drop the two 'scale' columns -> only translations+rotation
        x,y=xy[:,0],xy[:,1]; r=np.hypot(x,y)
        n_=len(r); dxi=L*(x/r)/r; deta=L*(y/r)/r
        base=[(np.ones(n_),0),(np.ones(n_),1),(y,0),(-x,1)]  # translations + rotation only
        N=2*n_; A_=np.zeros((N,1+len(base))); A_[:n_,0]=dxi; A_[n_:,0]=deta
        for j,(v,ax) in enumerate(base):
            if ax==0: A_[:n_,1+j]=v
            else: A_[n_:,1+j]=v
        fixed=np.sqrt(np.linalg.pinv(A_.T@A_)[0,0])
        f.append(free/fixed)
    print(f"  {name}: penalty for marginalising over plate scale/shear = x{np.median(f):.2f}")
