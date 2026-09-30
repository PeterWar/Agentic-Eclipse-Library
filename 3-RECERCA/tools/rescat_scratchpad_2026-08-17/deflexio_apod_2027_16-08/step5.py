import numpy as np, eb_core as E
rng=np.random.default_rng(31); RS=E.RSUN27

def leak_generic(hw,hh,prof_fn,order,trials=40,fix_scale=False,Vlim=11.0):
    out=[]
    for _ in range(trials):
        x,y,V=E.sample_rect(hw,hh,Vlim,rng,rmin_rho=2.0)
        r=np.hypot(x,y); ux,uy=x/r,y/r
        p=prof_fn(r/RS, r.max()/RS)
        out.append(E.bias_eps(x,y,1.0,(p*ux,p*uy),order=order,fix_scale=fix_scale))
    return np.median(out)

TR={'A':(7.14/2,4.77/2),'B':(4.17/2,2.78/2)}
print("="*80); print("BIAS IN epsilon FROM EACH COHERENT TERM"); print("="*80)

# 1. coronal gradient, uncorrected (constant background only).  Empirical profile
#    from the numerical fit: -0.37" at 3 Rsun, -0.106 at 4, -0.013 at 6, -0.004 at 8
#    -> fits d(rho) = -C * rho^-5.6 ; anchor at 3 Rsun = -0.37"
rr=np.array([3.,4.,6.,8.]); dd=np.array([0.374,0.1055,0.0126,0.0044])
p=np.polyfit(np.log(rr),np.log(dd),1); print(f"coronal-gradient profile: d ∝ rho^{p[0]:.2f}, "
      f"-0.37\" at 3 Rsun  (inward)")
def cor_prof(rho,redge,anchor=0.374): return -anchor*(rho/3.0)**p[0]
for t,(hw,hh) in TR.items():
    for o in [1,3]:
        print(f"  corona uncorrected (const bkg)   train {t}, order {o}: "
              f"Delta(eps) = {leak_generic(hw,hh,cor_prof,o):+.3f}")
print("  corona with a fitted background plane: bias < 0.007\" per star -> Delta(eps) < 0.001")

# 2. cubic optical distortion
print()
for A in [1.0,0.100,0.020,0.005]:
    row=f"  cubic distortion {A*1000:6.0f} mas at field edge:"
    for t,(hw,hh) in TR.items():
        for o in [1,3]:
            v=leak_generic(hw,hh,lambda r,re,A=A: A*(r/re)**3,o)
            row+=f"   {t}/o{o} {v:+.4f}"
    print(row)

# 3. plate-scale error IMPORTED from a calibration frame (scale held fixed)
print()
for ppm in [1,3,10,22,100]:
    row=f"  imported scale error {ppm:4d} ppm (scale FIXED):"
    for t,(hw,hh) in TR.items():
        v=leak_generic(hw,hh,lambda r,re,s=ppm*1e-6: s*r*RS,1,fix_scale=True)
        row+=f"   {t} {v:+.4f}"
    print(row+"      [scale FREE -> 0.000 exactly]")

# 4. differential refraction residual (Luxor, alt 81.73 deg)
print()
def refr_bennett(alt_deg,P=1005.,T=38.):
    a=np.radians(alt_deg)
    R=1.0/np.tan(np.radians(alt_deg+7.31/(alt_deg+4.4)))/60.  # deg
    return R*3600.*(P/1010.)*(283./(273.+T))
alt=81.73
for fov in [2.0,3.0]:
    d=np.linspace(-fov,fov,2001)
    Rr=np.array([refr_bennett(alt+dd) for dd in d])
    # remove the linear (affine) part -> what a plate model cannot absorb
    c=np.polyfit(d,Rr,1); lin=np.polyval(c,d)
    c3=np.polyfit(d,Rr,3); cub=np.polyval(c3,d)
    print(f"  refraction over +/-{fov:.0f} deg at alt {alt}: total {Rr.max()-Rr.min():.3f}\","
          f" after linear {np.abs(Rr-lin).max():.4f}\", after cubic {np.abs(Rr-cub).max():.5f}\"")
print("  (same computation at Leon, alt 9.2 deg:)")
for fov in [2.0]:
    d=np.linspace(-fov,fov,2001)
    Rr=np.array([refr_bennett(9.2+dd,925.,25.) for dd in d])
    c=np.polyfit(d,Rr,1); c3=np.polyfit(d,Rr,3)
    print(f"    total {Rr.max()-Rr.min():.2f}\", after linear {np.abs(Rr-np.polyval(c,d)).max():.2f}\","
          f" after cubic {np.abs(Rr-np.polyval(c3,d)).max():.3f}\"")
