import numpy as np, pickle
d=pickle.load(open("final.pkl","rb"))
xs,ys,snr,r,SH,sA,sB,sC,nd,flx=d['xs'],d['ys'],d['snr'],d['r'],d['SH'],d['sA'],d['sB'],d['sC'],d['nd'],d['flx']
import collections
print("radial distribution of stack peaks >5.5 sigma:")
for lo,hi in [(0,1.05),(1.05,1.3),(1.3,2),(2,3),(3,4),(4,6),(6,9),(9,20)]:
    k=(r>=lo)&(r<hi); print(f"  R/Rs [{lo:4.1f},{hi:5.1f}): {k.sum():5d}")
print()
sel=np.nonzero(r>1.6)[0]; sel=sel[np.argsort(-snr[sel])]
print(f"{'x':>6}{'y':>6}{'R/Rs':>6}{'stack':>7}{'grpA':>7}{'grpB':>7}{'grpC':>7}{'nfr':>4}{'FWHM':>6}{'b/a':>6}{'ang':>6}{'peak':>8}")
for i in sel[:60]:
    print(f"{xs[i]:6d}{ys[i]:6d}{r[i]:6.2f}{snr[i]:7.1f}{sA[i]:7.1f}{sB[i]:7.1f}{sC[i]:7.1f}{nd[i]:4d}"
          f"{SH[i,0]:6.2f}{SH[i,4]:6.2f}{SH[i,3]:6.0f}{flx[i]:8.1f}")
