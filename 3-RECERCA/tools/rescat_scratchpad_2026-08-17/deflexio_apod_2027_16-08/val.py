import numpy as np, eb_core as E
rng = np.random.default_rng(11)

def rect(n, hw, hh, rmin, rsun, rng):
    hw*=3600; hh*=3600; xs=[]; ys=[]
    while len(xs)<n:
        x=rng.uniform(-hw,hw); y=rng.uniform(-hh,hh)
        if np.hypot(x,y)>=rmin*rsun: xs.append(x); ys.append(y)
    return np.array(xs), np.array(ys)

print("="*74); print("VALIDATION 1 -- the 2026 Leon result (rectangular footprints)"); print("="*74)
for lab,n,hw,hh,s,rep in [("train A",38,7.14/2,4.77/2,1.61,1.39),
                          ("train B",22,4.17/2,2.78/2,0.64,0.57)]:
    o=[];f=[];nv=[]
    for _ in range(800):
        x,y = rect(n,hw,hh,2.16,E.RSUN26,rng)
        o.append(E.sigma_eps(x,y,s,rsun=E.RSUN26))
        f.append(E.sigma_eps(x,y,s,rsun=E.RSUN26,fix_scale=True))
        nv.append(E.sigma_eps_naive(x,y,s,rsun=E.RSUN26))
    o,f,nv = map(np.median,(o,f,nv))
    print(f"  {lab}: sigma(eps) model {o:.3f} vs reported {rep}   "
          f"[naive {nv:.3f}, D_total={o/nv:.2f}, scale-fixed {f:.3f}]")
    if lab=="train A": A=o
    else: B=o
print(f"  combined model {1/np.sqrt(1/A**2+1/B**2):.3f} vs reported 0.53  "
      f"-> model is {100*(1/np.sqrt(1/A**2+1/B**2))/0.53-100:+.0f}%")

print(); print("="*74); print("VALIDATION 2 -- Bruns 2017"); print("="*74)
o=[];f=[]
for _ in range(800):
    rho = np.sqrt(rng.uniform(2.433**2,4.817**2,18)); th=rng.uniform(0,2*np.pi,18)
    rho = np.concatenate([rho,[1.513,1.603]]); th=np.concatenate([th,rng.uniform(0,2*np.pi,2)])
    r=rho*945.0; x,y=r*np.cos(th),r*np.sin(th)
    o.append(E.sigma_eps(x,y,0.065,rsun=945.0))
    f.append(E.sigma_eps(x,y,0.065,rsun=945.0,fix_scale=True))
print(f"  scale solved in the eclipse frame : {100*np.median(o):.2f}%  (Bruns: ~4%)")
print(f"  scale from calibration fields     : {100*np.median(f):.2f}%  (Bruns fit term: 3.1%)")
print(f"  scale-degeneracy penalty D_scale  : {np.median(o)/np.median(f):.2f}x")

print(); print("="*74); print("VALIDATION 3 -- photometric anchor"); print("="*74)
for V in [5.73,7.0,8.0,9.18,10.0]:
    snr,sg = E.star_sigma(V, 8.0, 63.3, 10.3, 1.0, 5.8, 9.15)
    print(f"  Leon, V={V:5.2f}: SNR={snr:6.1f}  photon centroid={sg:.3f}\"")
print("  (the campaign's faintest identified star was V=9.18 -> SNR 5.0: consistent)")
