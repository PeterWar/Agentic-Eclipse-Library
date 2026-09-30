import numpy as np, eb_core as E
from scipy.optimize import brentq
rng=np.random.default_rng(555); RS=E.RSUN27
EXT=10**(0.4*(0.37*6.03-0.20*1.011))
CFG={'A':dict(hw=7.14/2,hh=4.77/2,area=90.1,fwhm=5.4),
     'B':dict(hw=4.17/2,hh=2.78/2,area=63.3,fwhm=3.8)}
def sample(k,msky=11.5,snrmin=10.,attr=0.30,Vlim=13.5):
    c=CFG[k]; x,y,V=E.sample_rect(c['hw'],c['hh'],Vlim,rng,rmin_rho=2.0)
    rho=np.hypot(x,y)/RS
    snr,sph=E.star_sigma(V,rho,c['area'],240.,EXT,c['fwhm'],msky)
    m=snr>=snrmin; keep=rng.random(m.sum())>attr
    return x[m][keep],y[m][keep],sph[m][keep]

print("="*88)
print("EQUIVALENT-UNIFORM sigma OF THE PHOTON TERM  (the number that belongs in a budget)")
print("="*88)
SET={}
for k in ['A','B']:
    eq=[];se=[]
    for _ in range(30):
        x,y,sph=sample(k)
        s_ph=E.sigma_eps(x,y,sph,order=1)
        f=lambda u: E.sigma_eps(x,y,u,order=1)-s_ph
        eq.append(brentq(f,1e-4,5.0)); se.append(s_ph)
    SET[k]=(np.median(eq),np.median(se))
    print(f"  train {k}: photons alone give sigma(eps)={np.median(se):.4f}"
          f"  == a uniform per-star sigma of {np.median(eq):.3f}\"")

print("\n"+"="*88); print("PLATE-MODEL INADEQUACY: leakage of higher-order radial distortion")
print("="*88)
def design_n(x,y,order,rsun=RS):
    n=len(x); r=np.hypot(x,y); rho=r/rsun; ux,uy=x/r,y/r
    xs,ys=x/r.max(),y/r.max(); cols=[]
    for o in range(0,order+1):
        for i in range(o+1):
            t=xs**(o-i)*ys**i
            cols+= [(t,np.zeros(n)),(np.zeros(n),t)]
    cols.append((E.L_GR*ux/rho,E.L_GR*uy/rho))
    A=np.zeros((2*n,len(cols)))
    for j,(cx,cy) in enumerate(cols): A[0::2,j]=cx; A[1::2,j]=cy
    return A
def leak_n(k,npow,order,trials=25):
    out=[]
    for _ in range(trials):
        x,y,_=sample(k)
        r=np.hypot(x,y); ux,uy=x/r,y/r; prof=(r/r.max())**npow
        A=design_n(x,y,order); w=np.ones(2*len(x))
        C=np.linalg.pinv(A.T@A,rcond=1e-13)
        d=np.empty(2*len(x)); d[0::2]=prof*ux; d[1::2]=prof*uy
        out.append((C@(A.T@d))[-1])
    return np.median(out)
print(f"{'radial pattern':16s}"+"".join(f"{f'plate order {o}':>16s}" for o in [1,2,3,5]))
for npow,nm in [(3,'r^3'),(5,'r^5'),(7,'r^7'),(2,'r^2 (asym)')]:
    print(f"{nm:16s}"+"".join(f"{leak_n('A',npow,o):16.4f}" for o in [1,2,3,5]))
print("  Delta(eps) per arcsec of radial residual at the field edge (train A)")

print("\n"+"="*88); print("SENSITIVITY OF THE FORECAST"); print("="*88)
for msky,snrmin,attr,lbl in [(12.0,7.,0.20,'optimistic sky 12.0, SNR>=7'),
                             (11.5,10.,0.30,'reference   sky 11.5, SNR>=10'),
                             (11.0,15.,0.40,'pessimistic sky 11.0, SNR>=15')]:
    r={}
    for k in ['A','B']:
        n=[];s=[]
        for _ in range(20):
            x,y,sph=sample(k,msky,snrmin,attr); n.append(len(x))
            s.append(E.sigma_eps(x,y,np.sqrt(sph**2+0.10**2),order=1))
        r[k]=(np.median(n),np.median(s))
    comb=1/np.sqrt(1/r['A'][1]**2+1/r['B'][1]**2)
    print(f"  {lbl:32s} N={r['A'][0]:5.0f}/{r['B'][0]:4.0f}"
          f"  sigma(eps)={comb:.4f}  ({100*comb:.1f}%)   [floor 0.10\"]")
