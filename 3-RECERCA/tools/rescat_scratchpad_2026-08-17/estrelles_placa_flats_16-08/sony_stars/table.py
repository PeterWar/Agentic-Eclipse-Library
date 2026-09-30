import numpy as np
d=np.load("meas.npz",allow_pickle=True)
RSUN=293.0; SC=3.234
cx,cy,r,snr,fw,ba,ang=d['cx'],d['cy'],d['r'],d['snr'],d['fw'],d['ba'],d['ang']
FA,EA,FC,EC,FT,ET,nd,DK,SN=d['FA'],d['EA'],d['FC'],d['EC'],d['FT'],d['ET'],d['nd'],d['DK'],d['SN']
names=list(d['names'])
sA=FA/np.maximum(EA,1e-9); sC=FC/np.maximum(EC,1e-9); sT=FT/np.maximum(ET,1e-9)
rs=r/RSUN
print("radial distribution of 5-sigma stack peaks:")
for lo,hi in [(0,1.1),(1.1,1.5),(1.5,2.5),(2.5,4),(4,6),(6,10),(10,20)]:
    k=(rs>=lo)&(rs<hi); print(f"  R/Rs [{lo:4.1f},{hi:5.1f}): {k.sum():5d}   of which A&C>3sigma: {(k&(sA>3)&(sC>3)).sum():4d}")
print()
star=(rs>1.5)&(sA>3.0)&(sC>3.0)&(fw>1.8)&(fw<6.5)&(ba>0.55)&np.isfinite(cx)
print(f"PSF-like AND present in both pointing groups, R>1.5Rsun : {star.sum()}")
o=np.nonzero(star)[0]; o=o[np.argsort(-snr[o])]
print(f"\n{'#':>3}{'x':>8}{'y':>8}{'R/Rs':>6}{'R(deg)':>7}{'SNR':>7}{'grpA':>7}{'grpC':>7}{'nfr':>4}{'FWHM_px':>8}{'FWHM_as':>8}{'b/a':>5}{'flux':>9}{'ferr':>7}{'dark':>6}")
for i in o[:70]:
    print(f"{list(o).index(i)+1:3d}{cx[i]:8.1f}{cy[i]:8.1f}{rs[i]:6.2f}{r[i]*SC/3600:7.2f}{snr[i]:7.1f}{sA[i]:7.1f}{sC[i]:7.1f}{nd[i]:4d}"
          f"{fw[i]:8.2f}{fw[i]*SC:8.1f}{ba[i]:5.2f}{FT[i]:9.1f}{ET[i]:7.1f}{DK[i].max():6.0f}")
