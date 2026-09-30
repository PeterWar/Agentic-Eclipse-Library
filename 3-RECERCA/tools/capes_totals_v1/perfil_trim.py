"""Capa PERFIL: retalla l'arrissat radial fi del compost final (per canal), d'1,2 a 2,9 R☉ amb rampes.
No toca res per sota d'1,15 (limbe/perles) ni per sobre de 3,0 (exterior = benchmark)."""
import os, sys, numpy as np
from scipy.ndimage import gaussian_filter1d
D = os.path.dirname(os.path.abspath(__file__))
W,H=7648,5353; SOL=(4021.35,2737.90); R_SOL=446.15
yy,xx=np.mgrid[0:H,0:W].astype(np.float32); r=np.hypot(xx-SOL[0],yy-SOL[1])/R_SOL
def sstep(t):
    t=np.clip(t,0,1); return t*t*t*(t*(t*6-15)+10)
nomv = sys.argv[1]
import tifffile
cand = np.load(os.path.join(D, f'compost_{nomv}.npy')).astype(np.float32)/65535.0
bench = tifffile.imread(os.path.expanduser('~/Downloads/Benchmark20Agost.tif')).astype(np.float32)/65535.0
rb=np.arange(1.0,3.4,0.01); rcx=0.5*(rb[:-1]+rb[1:])
idx=np.digitize(r.ravel(),rb)-1
med=np.full((len(rb)-1,3),np.nan,np.float32); medb=np.full((len(rb)-1,3),np.nan,np.float32)
flat=cand.reshape(-1,3); flatb=bench.reshape(-1,3)
for k in range(len(rb)-1):
    s=idx==k
    if s.sum()>200:
        med[k]=np.median(flat[s],axis=0); medb[k]=np.median(flatb[s],axis=0)
ok=~np.isnan(med[:,0])
delta=np.zeros_like(med)
for c in range(3):
    d=gaussian_filter1d(medb[ok,c]-med[ok,c],3.0,mode='nearest')
    delta[ok,c]=d
w=sstep((rcx-1.28)/0.10)*sstep((3.05-rcx)/0.15)
delta*=w[:,None]
dmap=np.zeros((H,W,3),np.float32)
for c in range(3):
    dmap[...,c]=np.interp(r,rcx,delta[:,c],left=0,right=0)
out=np.clip(cand+dmap,0,1)
np.save(os.path.join(D,f'compost_{nomv}_trim.npy'),np.clip(np.rint(out*65535),0,65535).astype(np.uint16))
np.savez(os.path.join(D,f'perfil_trim_{nomv}.npz'),rcx=rcx,delta=delta)
print(nomv,'|delta| màx:',float(np.abs(delta).max()),'p99:',float(np.percentile(np.abs(delta),99)))
