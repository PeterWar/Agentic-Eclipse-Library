import numpy as np, eb_core as E
rng=np.random.default_rng(101); RS=E.RSUN27
EXT=10**(0.4*(0.37*6.03-0.20*1.011))
CFG={'A':dict(hw=7.14/2,hh=4.77/2,area=90.1,fwhm=5.4),
     'B':dict(hw=4.17/2,hh=2.78/2,area=63.3,fwhm=3.8)}

def sample(k, msky, snrmin, attrition, Vlim=13.5, seed=None):
    c=CFG[k]
    x,y,V=E.sample_rect(c['hw'],c['hh'],Vlim,rng,rmin_rho=2.0)
    rho=np.hypot(x,y)/RS
    snr,sph=E.star_sigma(V,rho,c['area'],240.,EXT*1.0,c['fwhm'],msky)
    m=snr>=snrmin
    keep=rng.random(m.sum())>attrition
    return x[m][keep],y[m][keep],rho[m][keep],sph[m][keep]

print("="*86)
print("REFERENCE 2027 SAMPLE  (conservative: sky 11.5, SNR>=10, 30% attrition for")
print("blends / doubles / variables / frame edges).  240 s on the eclipse field.")
print("="*86)
print(f"{'train':6} {'N':>6} {'W=sum(Rs/r)^2':>14} {'sqrt(W)':>8} {'D(scale free)':>14} {'D(scale fixed)':>15}")
REF={}
for k in ['A','B']:
    N=[];W=[];D1=[];D2=[];PH=[]
    for _ in range(40):
        x,y,rho,sph=sample(k,11.5,10.,0.30)
        N.append(len(x)); W.append(np.sum(1/rho**2))
        n=E.sigma_eps_naive(x,y,1.0)
        D1.append(E.sigma_eps(x,y,1.0,order=1)/n)
        D2.append(E.sigma_eps(x,y,1.0,order=1,fix_scale=True)/n)
        w=(1/rho**2); PH.append(np.sqrt(np.sum(w*sph**2)/np.sum(w)))
    REF[k]=(np.median(N),np.median(W),np.median(D1),np.median(D2),np.median(PH))
    print(f"{k:6} {REF[k][0]:6.0f} {REF[k][1]:14.1f} {np.sqrt(REF[k][1]):8.2f}"
          f" {REF[k][2]:14.2f} {REF[k][3]:15.2f}")
    print(f"       weight-averaged PHOTON centroid error = {REF[k][4]:.3f}\"")

print("\n"+"="*86)
print("REQUIRED PER-STAR SIGMA:  sigma_star = sigma(eps) * L * sqrt(W) / D")
print("="*86)
tg=[("(a) 3-sigma detection of deflection",1/3.),
    ("(b) 5-sigma Einstein vs Newton",0.1),
    ("(c) 3% on the deflection coefficient",0.03)]
for lab,t in tg:
    tc=t*np.sqrt(2)      # each train carries half the information
    print(f"\n {lab}   sigma(eps)<= {t:.4f}")
    for k in ['A','B']:
        N,W,D1,D2,PH=REF[k]
        print(f"   train {k} (N={N:.0f}, sqrt(W)={np.sqrt(W):.2f}):"
              f"  alone {t*E.L_GR*np.sqrt(W)/D1:7.3f}\" |"
              f"  as half of the pair {tc*E.L_GR*np.sqrt(W)/D1:7.3f}\" |"
              f"  with scale fixed {tc*E.L_GR*np.sqrt(W)/D2:7.3f}\"")
    print(f"   -> 3rd-order plate model instead of 1st: multiply the requirement by ~0.66")

print("\n"+"="*86); print("SEEING (Zacharias 1996 empirical law)"); print("="*86)
def zach(seeing, T, fov_arcmin, D_m, z_deg):
    s_an=3e-3*seeing*(0.9/D_m)**(1/6.)
    return s_an*np.sqrt(100./T)*(fov_arcmin/20.)**(1/3.)/np.cos(np.radians(z_deg))
for lab,fov,D in [('train A (4.3 deg half-diag)',258,0.107),('train B (2.5 deg)',150,0.0898)]:
    for see in [2.,3.,5.]:
        print(f"  {lab}, seeing {see:.0f}\": per 10 s frame "
              f"{1000*zach(see,10,fov,D,8.3):6.1f} mas | over 240 s {1000*zach(see,240,fov,D,8.3):5.1f} mas")
print("  Leon 2026 for comparison (seeing 3\", 10.3 s, z=80.8): "
      f"{1000*zach(3,10.3,150,0.0898,80.8):.0f} mas per frame, "
      f"{1000*zach(3,103.7,150,0.0898,80.8):.0f} mas over the whole totality")

print("\n"+"="*86); print("TRAILING"); print("="*86)
for lab,pa,fw in [('A',3.202,5.4),('B',2.1495,3.8)]:
    sg=fw/2.3548
    for drift,dl in [(0.041,'solar rate: the STARS trail at 0.041\"/s'),
                     (0.022,'sidereal, 5 arcmin polar error'),
                     (0.610,'2026 as flown (2 deg polar error)')]:
        for t in [10.,30.]:
            T=drift*t; sa=np.sqrt(sg**2+T**2/12)
            print(f"  train {lab}, {t:4.0f} s, {dl:38s}: trail {T:5.2f}\" -> "
                  f"centroid x{(sa/sg)**1.5:.2f} along-trail")
        break
