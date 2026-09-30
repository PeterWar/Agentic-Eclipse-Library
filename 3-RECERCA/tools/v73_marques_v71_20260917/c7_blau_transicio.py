"""C7: d'on surt el blau de la transició? RGB de la base (3, sense mirar el suport) i de la capa lunar (30) a d = −4…+6 de la vora lunar, per sectors; i el compost sense filtres capa a capa (base sola sota la vora)."""
import sys, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; S3='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
sys.path.insert(0,NEW)
import compo71; from compo71 import *
from scipy.ndimage import map_coordinates, gaussian_filter1d
CX,CY,RS=998.88,998.41,456.0; Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY)
d30=np.load(NEW+'/roi72_L30.npz'); cov=(d30['c-1'].astype(np.float64)/65535)*(d30['c-2'].astype(np.float64)/65535)
TH=np.deg2rad(np.arange(0,360,0.25)); RR=np.arange(430,480,0.25); xs=CX+RR[None,:]*np.cos(TH[:,None]); ys=CY-RR[None,:]*np.sin(TH[:,None])
P=map_coordinates(cov,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(RR)); Redge=np.full(len(TH),np.nan)
for i in range(len(TH)):
    j=np.nonzero(np.diff(np.sign(P[i]-0.5))!=0)[0]
    if len(j): k=j[-1]; Redge[i]=RR[k]+(0.5-P[i][k])/(P[i][k+1]-P[i][k]+1e-9)*0.25
ok=np.isfinite(Redge); Redge[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],Redge[ok]); Redge=gaussian_filter1d(Redge,4,mode='wrap')
D=np.arange(-4,7,1.0)
def polar_d(F): xs2=CX+(Redge[:,None]+D[None,:])*np.cos(TH[:,None]); ys2=CY-(Redge[:,None]+D[None,:])*np.sin(TH[:,None]); return map_coordinates(F,[ys2.ravel(),xs2.ravel()],order=1).reshape(len(TH),len(D))
d3=np.load(NEW+'/roi72_L3.npz'); rgb3=np.dstack([d3['c0'],d3['c1'],d3['c2']]).astype(np.float64)/65535; a3=(d3['c-1'].astype(np.float64)/65535)*(d3['c-2'].astype(np.float64)/65535)
rgb30=np.dstack([d30['c0'],d30['c1'],d30['c2']]).astype(np.float64)/65535
d57=np.load(NEW+'/roi71_L57.npz'); rgb57=np.dstack([d57['c0'],d57['c1'],d57['c2']]).astype(np.float64)/65535; a57=(d57['c-1'].astype(np.float64)/65535)*(d57['c-2'].astype(np.float64)/65535)
print('d des de la vora lunar:      '+' '.join(f'{int(x):5d}' for x in D))
for nom,rgb,a in (('base 3',rgb3,a3),('lunar 30',rgb30,cov),('POWAAAH3 57',rgb57,a57)):
    for tag,F in (('alfa',a),('L',rgb.mean(-1)),('R/G',rgb[...,0]/np.maximum(rgb[...,1],1e-4)),('B/G',rgb[...,2]/np.maximum(rgb[...,1],1e-4))):
        Pq=polar_d(F); print(f'{nom:12s} {tag:4s} sector E 0–60: '+' '.join(f'{x:5.2f}' for x in np.median(Pq[(np.rad2deg(TH)<60)],0))+'   | S 240–300: '+' '.join(f'{x:5.2f}' for x in np.median(Pq[(np.rad2deg(TH)>=240)&(np.rad2deg(TH)<300)],0)))
# compost sense filtres capa a capa: base sola; base+57; base+57+30
compo71.OVERRIDE.clear()
for lid in (3,55,56,76,96,204): compo71.OVERRIDE[lid]=NEW+f'/roi72_L{lid}.npz'
compo71.OVERRIDE[30]=NEW+'/roi72_L30.npz'
for ids,nom in (([3],'base sola'),([3,57],'base + POWAAAH3'),([3,57,30],'base + 57 + lunar'),([3,30],'base + lunar (sense 57)')):
    C,a=recompon(ids=ids); bg=polar_d(C[...,2]/np.maximum(C[...,1],1e-4)); Lc=polar_d(C.mean(-1)); al=polar_d(a)
    print(f'{nom:24s} B/G E: '+' '.join(f'{x:5.2f}' for x in np.median(bg[np.rad2deg(TH)<60],0))+' · L: '+' '.join(f'{x:5.2f}' for x in np.median(Lc[np.rad2deg(TH)<60],0))+' · alfa: '+' '.join(f'{x:5.2f}' for x in np.median(al[np.rad2deg(TH)<60],0)))
