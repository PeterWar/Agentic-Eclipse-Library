import numpy as np
d=np.load("meas.npz",allow_pickle=True)
RSUN=293.;SC=3.234
cx,cy,r,snr,fw,ba=d['cx'],d['cy'],d['r'],d['snr'],d['fw'],d['ba']
FA,EA,FC,EC,FT,ET,nd,SN,DK=d['FA'],d['EA'],d['FC'],d['EC'],d['FT'],d['ET'],d['nd'],d['SN'],d['DK']
names=list(d['names']); rs=r/RSUN
sA=FA/np.maximum(EA,1e-9); sC=FC/np.maximum(EC,1e-9)
k=np.nonzero((rs>3.5)&np.isfinite(cx))[0]; k=k[np.argsort(-snr[k])]
print(f"ALL stack peaks >5 sigma with R>3.5 Rsun : {len(k)}")
print(f"{'x':>8}{'y':>8}{'R/Rs':>6}{'SNR':>7}{'grpA':>7}{'grpC':>7}{'nfr':>4}{'FWHM':>6}{'b/a':>5}{'flux':>8}  per-frame SNR: "+" ".join(f"{n[3:]:>5}" for n in names))
for i in k:
    print(f"{cx[i]:8.1f}{cy[i]:8.1f}{rs[i]:6.2f}{snr[i]:7.1f}{sA[i]:7.1f}{sC[i]:7.1f}{nd[i]:4d}{fw[i]:6.2f}{ba[i]:5.2f}{FT[i]:8.0f}   "
          +" ".join(f"{SN[i,j]:5.1f}" for j in range(len(names))))
