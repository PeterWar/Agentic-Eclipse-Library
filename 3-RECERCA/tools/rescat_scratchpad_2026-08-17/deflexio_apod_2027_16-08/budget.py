import numpy as np
np.random.seed(21)
LDEF=1.7516; RSUN=945.6

r=np.sqrt(np.random.uniform(2**2,15**2,80000)); th=np.random.uniform(0,2*np.pi,len(r))
x,y=r*np.cos(th),r*np.sin(th)
def leak(bfun,order=1):
    b=bfun(r); Rn=r.max(); X,Y=x/Rn,y/Rn; cols=[np.ones_like(x)]
    for o in range(1,order+1):
        for i in range(o+1): cols.append(X**(o-i)*Y**i)
    M=np.array(cols).T; n,m=M.shape; Z=np.zeros((n,m))
    Jx=np.hstack([M,Z,(LDEF/r*(x/r))[:,None]]); Jy=np.hstack([Z,M,(LDEF/r*(y/r))[:,None]])
    J=np.vstack([Jx,Jy]); d=np.concatenate([b*(x/r),b*(y/r)])
    return np.linalg.lstsq(J,d,rcond=None)[0][-1]

print("="*84); print("LEAKAGE, extended: which systematics the plate model DOES absorb")
print("  amplitude normalised to 1 arcsec at the FIELD EDGE (15 Rsun) for growing patterns,")
print("  and to 1 arcsec at 2 Rsun for falling ones"); print("="*84)
rows=[("r    (plate scale)",   lambda rr: rr/15.0),
      ("r^2  (2nd-order dist)",lambda rr: (rr/15.0)**2),
      ("r^3  (cubic distortion)",lambda rr:(rr/15.0)**3),
      ("r^5  (5th-order dist)", lambda rr:(rr/15.0)**5),
      ("1/r  (= deflection)",   lambda rr: 2.0/rr),
      ("1/r^2",                 lambda rr:(2.0/rr)**2),
      ("1/r^4.65 (coronal grad)",lambda rr:(2.0/rr)**4.65),
      ("constant inward",       lambda rr: np.ones_like(rr))]
print(f"{'pattern':>24} {'linear(6p)':>12} {'quad(12p)':>11} {'cubic(20p)':>12} {'5th(42p)':>10}")
for lab,f in rows:
    print(f"{lab:>24} {leak(f,1):12.4f} {leak(f,2):11.4f} {leak(f,3):12.4f} {leak(f,5):10.4f}")

print()
print("="*84); print("VALUE OF OFFSET CALIBRATION FIELDS IN 2027 (variance inflation)")
print("="*84)
def sig_eps(rin,rout,N,sper,order=1,fix_scale=False):
    rr=np.sqrt(np.random.uniform(rin**2,rout**2,N)); tt=np.random.uniform(0,2*np.pi,N)
    xx,yy=rr*np.cos(tt),rr*np.sin(tt); Rn=rr.max(); X,Y=xx/Rn,yy/Rn
    cols=[np.ones_like(X)]
    for o in range(1,order+1):
        for i in range(o+1): cols.append(X**(o-i)*Y**i)
    M=np.array(cols).T; n,m=M.shape; Z=np.zeros((n,m))
    Jx=np.hstack([M,Z]); Jy=np.hstack([Z,M])
    if fix_scale:
        v=np.zeros(2*m); v[1]=1; v[m+2]=1; v/=np.linalg.norm(v)
        P=np.eye(2*m)-np.outer(v,v); Jx=Jx@P; Jy=Jy@P
    Jx=np.hstack([Jx,(LDEF/rr*(xx/rr))[:,None]]); Jy=np.hstack([Jy,(LDEF/rr*(yy/rr))[:,None]])
    F=Jx.T@Jx+Jy.T@Jy; C=np.linalg.pinv(F,rcond=1e-12)
    return np.sqrt(C[-1,-1])*sper
print(f"{'geometry':>28} {'order':>6} {'scale free':>11} {'scale fixed':>12} {'gain':>7}")
for lab,a,b,N in [("Bruns 2017 (2.4-4.8)",2.43,4.82,20),
                  ("2026 train B (2.2-9.5)",2.16,9.5,22),
                  ("2027 narrow (2-8)",2.0,8.0,400),
                  ("2027 wide  (2-15)",2.0,15.0,1500),
                  ("2027 very wide (2-20)",2.0,20.0,2500)]:
    for order in (1,3):
        f=sig_eps(a,b,N,0.15,order,False); g=sig_eps(a,b,N,0.15,order,True)
        print(f"{lab:>28} {order:6d} {f:11.4f} {g:12.4f} {f/g:7.3f}")

print()
print("="*84); print("COST OF THE 3rd-ORDER PLATE MODEL vs FIELD RICHNESS (sper=0.15\")")
print("="*84)
print(f"{'stars':>7} {'r range':>10} {'linear':>9} {'quad':>9} {'cubic':>9} {'5th':>9}")
for N,a,b in [(30,2,5),(100,2,8),(400,2,12),(1500,2,15),(3800,2,15)]:
    print(f"{N:7d} {f'{a}-{b}':>10} "+" ".join(f"{sig_eps(a,b,N,0.15,o):9.4f}" for o in (1,2,3,5)))

print()
print("="*84); print("DIFFERENTIAL ABERRATION & REFRACTION over a 4-deg-radius field")
print("="*84)
K=20.4955   # aberration constant, arcsec
for fr in [1.0,2.0,3.0,4.0]:
    th_=np.radians(fr)
    lin = K*th_                      # differential aberration, linear part (arcsec)
    nl  = K*th_**2/2                 # leading non-linear part
    print(f"  field radius {fr:.1f} deg: differential aberration linear {lin:7.3f}\"  "
          f"2nd-order {nl:7.4f}\"")
# refraction at Luxor
def bennett(a,P=1005.,T=40.):
    R=1.0/np.tan(np.radians(a+7.31/(a+4.4))); return R*(P/1010.)*(283./(273.+T))*60.
alt=81.77
for fr in [1.0,2.0,3.0,4.0]:
    d1=(bennett(alt-fr)-bennett(alt+fr))/(2*fr)          # arcsec per deg
    lin=d1*fr
    quad=(bennett(alt-fr)+bennett(alt+fr)-2*bennett(alt))/2
    print(f"  field radius {fr:.1f} deg: refraction linear {lin:7.3f}\"  quadratic {quad:8.4f}\"")

print()
print("="*84); print("PARALLACTIC ROTATION OF THE REFRACTION SHEAR DURING TOTALITY (Luxor)")
print("="*84)
comp=2.67e-4                     # vertical compression at alt 81.77
dq=np.radians(9.68)              # rotation of the alt-az frame over 383 s
for fr in [1.0,2.0,3.0,4.0]:
    amp=comp*fr*3600             # arcsec of shear displacement at field radius fr
    print(f"  field radius {fr:.1f} deg: shear amplitude {amp:6.3f}\"  ; "
          f"change if the shear axis rotates 9.68 deg and you ignore it: {amp*2*np.sin(dq/2):6.3f}\"")
