import numpy as np, eb_core as E
rng=np.random.default_rng(1212); RS=E.RSUN27
EXT=10**(0.4*(0.37*6.03-0.20*1.011))
CFG={'A':dict(hw=7.14/2,hh=4.77/2,area=90.1,fwhm=5.4),
     'B':dict(hw=4.17/2,hh=2.78/2,area=63.3,fwhm=3.8)}
def s_eps(k,floor,order=1,msky=11.5,snrmin=10.,attr=.30):
    c=CFG[k]; v=[]
    for _ in range(30):
        x,y,V=E.sample_rect(c['hw'],c['hh'],13.5,rng,rmin_rho=2.0)
        rho=np.hypot(x,y)/RS
        snr,sph=E.star_sigma(V,rho,c['area'],240.,EXT,c['fwhm'],msky)
        m=snr>=snrmin; kp=rng.random(m.sum())>attr
        v.append(E.sigma_eps(x[m][kp],y[m][kp],np.sqrt(sph[m][kp]**2+floor**2),order=order))
    return np.median(v)
print("SCENARIO LADDER  (Luxor, 240 s, conservative sample, linear plate model)")
for lab,fA,fB,o in [("2026 hardware AND 2026 per-star performance, unchanged",1.61,0.64,1),
                    ("same, but with a 3rd-order plate model",1.61,0.64,3),
                    ("refraction+dispersion+trailing gone by geography alone",0.80,0.35,1),
                    ("+ r' filter, focus, sidereal tracking, Gaia DR3",0.35,0.20,1),
                    ("careful plan, 3rd-order plate model",0.154,0.113,3),
                    ("Bruns-class per-star error (0.065\")",0.065,0.065,3)]:
    a=s_eps('A',fA,o); b=s_eps('B',fB,o); c=1/np.sqrt(1/a**2+1/b**2)
    print(f"  {lab:56s} A {a:.4f} B {b:.4f} -> {c:.4f} ({100*c:.1f}%)  "
          f"GR {1/c:4.1f}sig  E-vs-N {0.5/c:4.1f}sig")
