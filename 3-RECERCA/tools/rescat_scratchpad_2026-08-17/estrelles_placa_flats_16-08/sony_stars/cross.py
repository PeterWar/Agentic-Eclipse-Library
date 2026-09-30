import numpy as np, pickle
from scipy import ndimage
from scipy.spatial import cKDTree
SA=np.load("SA.npy"); SC=np.load("SC.npy")
M=np.load("warpM.npy"); T=np.load("warpT.npy"); C0=np.load("warpC.npy")
moon=pickle.load(open("moon.pkl","rb")); RSUN=293.; SC_AS=3.234
CX,CY=moon['DSC06993'][0],moon['DSC06993'][1]
h,w=SA.shape
def peaks(S,thr):
    lm=(S>thr)&(S==ndimage.maximum_filter(S,13))
    lm[:45]=lm[-45:]=False; lm[:,:45]=lm[:,-45:]=False
    ys,xs=np.nonzero(lm)
    a=S[ys,xs-1];b=S[ys,xs];c=S[ys,xs+1];d=a-2*b+c; fx=np.where(d!=0,.5*(a-c)/np.where(d!=0,d,1),0)
    a=S[ys-1,xs];c=S[ys+1,xs];d=a-2*b+c; fy=np.where(d!=0,.5*(a-c)/np.where(d!=0,d,1),0)
    return np.c_[xs+np.clip(fx,-1,1),ys+np.clip(fy,-1,1)],b
PA,sa=peaks(SA,4.0); PC,sc=peaks(SC,4.0)
print(f"group A stack: {len(PA)} peaks >4 sigma ; group C stack: {len(PC)}")
PAw=(PA-C0)@M.T+T+C0
t=cKDTree(PC); d,i=t.query(PAw,distance_upper_bound=6.0)
ok=np.isfinite(d)
xa,ya=PA[ok,0],PA[ok,1]; xc,yc=PC[i[ok],0],PC[i[ok],1]
SNA=sa[ok]; SNC=sc[i[ok]]
rC=np.hypot(xc-CX,yc-CY)
print(f"matched within 6 px : {ok.sum()}")
# false-match rate: shift the A list by a large bogus offset and rematch
rng=np.random.default_rng(1); fake=0
for k in range(20):
    off=rng.uniform(-400,400,2)
    dd,_=t.query(PAw+off,distance_upper_bound=6.0); fake+=np.isfinite(dd).sum()
print(f"expected random coincidences at 6 px: {fake/20:.1f}")
np.savez("cross.npz",xa=xa,ya=ya,xc=xc,yc=yc,SNA=SNA,SNC=SNC,rC=rC,CX=CX,CY=CY)
for lo,hi in [(0,1.2),(1.2,2),(2,3),(3,5),(5,8),(8,20)]:
    k=(rC/RSUN>=lo)&(rC/RSUN<hi); print(f"  R/Rs [{lo:4.1f},{hi:5.1f}): matched={k.sum():5d}")
