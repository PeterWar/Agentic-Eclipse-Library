import numpy as np, eb_core as E
rng=np.random.default_rng(909); RS=E.RSUN27
EXT=10**(0.4*(0.37*6.03-0.20*1.011))
CFG={'A':dict(hw=7.14/2,hh=4.77/2,area=90.1,fwhm=5.4),
     'B':dict(hw=4.17/2,hh=2.78/2,area=63.3,fwhm=3.8)}
def sample(k,msky=11.5,snrmin=10.,attr=0.30):
    c=CFG[k]; x,y,V=E.sample_rect(c['hw'],c['hh'],13.5,rng,rmin_rho=2.0)
    rho=np.hypot(x,y)/RS
    snr,sph=E.star_sigma(V,rho,c['area'],240.,EXT,c['fwhm'],msky)
    m=snr>=snrmin; keep=rng.random(m.sum())>attr
    return x[m][keep],y[m][keep],sph[m][keep]

print("="*88); print("REQUIRED PER-STAR SIGMA, FINAL  (reference sample, both trains combined)")
print("="*88)
res={}
for k in ['A','B']:
    for o in [1,3]:
        v=[]
        for _ in range(30):
            x,y,_=sample(k)
            v.append(E.sigma_eps(x,y,1.0,order=o))      # sigma(eps) per 1 arcsec of per-star error
        res[(k,o)]=np.median(v)
print(f"{'':22}{'sigma(eps) per 1\" of per-star error':>38}")
for k in ['A','B']:
    print(f"  train {k}: linear plate model {res[(k,1)]:.5f}   3rd-order {res[(k,3)]:.5f}"
          f"   (cost of 3rd order x{res[(k,3)]/res[(k,1)]:.2f})")
print()
print(f"{'target':40s}{'linear model':>26s}{'3rd-order model':>26s}")
for lab,t in [("(a) 3sig detection: sig(e)<=0.333",1/3.),("(b) 5sig Einstein-Newton: <=0.100",0.10),
              ("(c) 3% coefficient: <=0.030",0.03)]:
    row=f"{lab:40s}"
    for o in [1,3]:
        tc=t*np.sqrt(2)
        row+=f"   A {tc/res[('A',o)]:6.3f}\" B {tc/res[('B',o)]:6.3f}\""
    print(row)

print("\n"+"="*88); print("SCALE: FIT IN-FRAME OR IMPORT FROM CALIBRATION FIELDS?"); print("="*88)
for k in ['A','B']:
    fr=[];fx=[]
    for _ in range(30):
        x,y,sph=sample(k); s=np.sqrt(sph**2+0.10**2)
        fr.append(E.sigma_eps(x,y,s,order=1)); fx.append(E.sigma_eps(x,y,s,order=1,fix_scale=True))
    fr,fx=np.median(fr),np.median(fx)
    # leakage of an imported scale error, per ppm
    lk=[]
    for _ in range(20):
        x,y,sph=sample(k); r=np.hypot(x,y)
        lk.append(E.bias_eps(x,y,np.sqrt(sph**2+0.10**2),(1e-6*x,1e-6*y),order=1,fix_scale=True))
    lk=np.median(lk)
    be=np.sqrt(max(fr**2-fx**2,0))/lk
    print(f"  train {k}: scale free {fr:.4f} | scale fixed {fx:.4f} | leak {lk:.4f} per ppm"
          f"  -> importing wins only if the calibration scale is better than {be:.2f} ppm")
print("  (Bruns achieved 3.34 ppm from two in-totality calibration fields)")

print("\n"+"="*88); print("DIFFERENTIAL REFRACTION RESIDUAL OVER EACH REAL FIELD"); print("="*88)
def refr(alt,P,T):
    return (1.0/np.tan(np.radians(alt+7.31/(alt+4.4))))/60.*3600.*(P/1010.)*(283./(273.+T))
for site,alt,P,T in [('Leon 2026',9.2,925.,25.),('Luxor 2027',81.73,1005.,38.)]:
    for k,hh in [('A',4.77/2),('B',2.78/2)]:
        d=np.linspace(-hh,hh,801); R=np.array([refr(alt+dd,P,T) for dd in d])
        l=np.abs(R-np.polyval(np.polyfit(d,R,1),d)).max()
        c=np.abs(R-np.polyval(np.polyfit(d,R,3),d)).max()
        print(f"  {site:11s} train {k} (+/-{hh:.2f} deg): total {R.max()-R.min():8.2f}\""
              f"  after linear {l:8.4f}\"  after cubic {c:8.5f}\"")

print("\n"+"="*88); print("THE INNER STARS: FWHM IS THE LEVER (corona-limited)"); print("="*88)
print(f"{'FWHM':>6} {'V=9 @2Rs':>10} {'V=10 @2Rs':>11} {'V=11 @2Rs':>11} {'V=11 @3Rs':>11}  (photon sigma, arcsec)")
for fw in [6.0,5.0,4.0,3.0,2.0,1.5]:
    r=f"{fw:6.1f}"
    for V,rho in [(9.,2.),(10.,2.),(11.,2.),(11.,3.)]:
        s,sg=E.star_sigma(V,rho,63.3,240.,EXT*1.3,fw,11.5)
        r+=f"{sg:11.3f}" if s>=7 else f"{'--':>11}"
    print(r)
print("  at 2-4 Rsun the K+F corona IS the sky: 6.9 mag/arcsec2 at 2 Rsun, 5 mag brighter")
print("  than the 11.5-12 totality sky. No site, aperture or filter changes it; only FWHM does,")
print("  and it enters SQUARED (sigma ~ 0.6*FWHM/SNR with SNR ~ 1/FWHM in the sky-limited case).")
