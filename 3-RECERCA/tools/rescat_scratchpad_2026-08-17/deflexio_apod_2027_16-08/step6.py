import numpy as np, eb_core as E
rng=np.random.default_rng(77); RS=E.RSUN27
EXT=10**(0.4*(0.37*6.03-0.20*1.011))

CFG={
 'A': dict(hw=7.14/2, hh=4.77/2, area=90.1, fwhm=5.4, thru=EXT*1.00),   # Bayer luminance
 'B': dict(hw=4.17/2, hh=2.78/2, area=63.3, fwhm=3.8, thru=EXT*1.00),
}
T_INT=240.; MSKY=12.0

def realise(c, floor, order=1, fix_scale=False, snrmin=7., Vlim=13.0, trials=25):
    ss=[];NN=[];frac=[]
    for _ in range(trials):
        x,y,V=E.sample_rect(c['hw'],c['hh'],Vlim,rng,rmin_rho=2.0)
        rho=np.hypot(x,y)/RS
        snr,sph=E.star_sigma(V,rho,c['area'],T_INT,c['thru'],c['fwhm'],MSKY)
        m=snr>=snrmin
        sig=np.sqrt(sph[m]**2+floor**2)
        ss.append(E.sigma_eps(x[m],y[m],sig,order=order,fix_scale=fix_scale))
        NN.append(m.sum())
        # weighted fraction of the *information* carried by the photon term
        w=(1/rho[m]**2)/sig**2
        frac.append(np.sum(w*sph[m]**2/sig**2)/np.sum(w))
    return np.median(ss),int(np.median(NN)),np.median(frac)

print("="*84)
print("2027 FORECAST  (Luxor, sky 12.0, 240 s on the eclipse field, SNR>=7, stars 2-16 Rsun)")
print("="*84)
print(f"{'floor (\")':>10} {'N_A':>5} {'sig(e) A':>9} {'N_B':>5} {'sig(e) B':>9} {'combined':>9}"
      f" {'E-vs-N':>8} {'as % of L':>10}")
for floor in [1.61,0.64,0.40,0.25,0.15,0.10,0.06,0.03]:
    sA,NA,_=realise(CFG['A'],floor); sB,NB,_=realise(CFG['B'],floor)
    comb=1/np.sqrt(1/sA**2+1/sB**2)
    print(f"{floor:10.2f} {NA:5d} {sA:9.4f} {NB:5d} {sB:9.4f} {comb:9.4f} {0.5/comb:8.1f} {100*comb:10.1f}")

print("\n  (the same table with the plate SCALE held fixed from calibration fields)")
print(f"{'floor (\")':>10} {'sig(e) A':>9} {'sig(e) B':>9} {'combined':>9}  gain")
for floor in [0.40,0.25,0.15,0.10,0.06]:
    sA,_,_=realise(CFG['A'],floor,fix_scale=True); sB,_,_=realise(CFG['B'],floor,fix_scale=True)
    c1=1/np.sqrt(1/sA**2+1/sB**2)
    sA2,_,_=realise(CFG['A'],floor); sB2,_,_=realise(CFG['B'],floor)
    c2=1/np.sqrt(1/sA2**2+1/sB2**2)
    print(f"{floor:10.2f} {sA:9.4f} {sB:9.4f} {c1:9.4f}  x{c2/c1:.2f}")

print("\n  (3rd-order plate model fitted in-frame -- the price of killing cubic distortion)")
print(f"{'floor (\")':>10} {'sig(e) A o1':>12} {'o3':>9} {'sig(e) B o1':>12} {'o3':>9} {'comb o3':>9}")
for floor in [0.25,0.15,0.10,0.06]:
    a1,_,_=realise(CFG['A'],floor,order=1); a3,_,_=realise(CFG['A'],floor,order=3)
    b1,_,_=realise(CFG['B'],floor,order=1); b3,_,_=realise(CFG['B'],floor,order=3)
    print(f"{floor:10.2f} {a1:12.4f} {a3:9.4f} {b1:12.4f} {b3:9.4f} "
          f"{1/np.sqrt(1/a3**2+1/b3**2):9.4f}")

print("\n"+"="*84)
print("HOW MUCH OF THE PER-STAR BUDGET IS ALREADY SPENT ON PHOTONS?")
print("="*84)
for k,c in CFG.items():
    for floor in [0.20,0.10]:
        s,N,f=realise(c,floor)
        print(f"  train {k}, floor {floor:.2f}\": N={N}, photon share of the weighted "
              f"variance = {100*f:.1f}%")
