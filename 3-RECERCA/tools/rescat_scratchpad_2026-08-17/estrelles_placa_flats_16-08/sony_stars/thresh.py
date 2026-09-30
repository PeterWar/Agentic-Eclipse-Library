import numpy as np, pickle
from scipy import ndimage
from scipy.spatial import cKDTree
SA=np.load("SA.npy"); SC=np.load("SC.npy")
M=np.load("warpM.npy"); T=np.load("warpT.npy"); C0=np.load("warpC.npy")
moon=pickle.load(open("moon.pkl","rb")); RSUN=293.
CX,CY=moon['DSC06993'][0],moon['DSC06993'][1]
def peaks(S,thr):
    lm=(S>thr)&(S==ndimage.maximum_filter(S,13))
    lm[:45]=lm[-45:]=False; lm[:,:45]=lm[:,-45:]=False
    ys,xs=np.nonzero(lm); return np.c_[xs,ys].astype(float),S[ys,xs]
rng=np.random.default_rng(7)
print(f"{'thr':>5}{'nA':>7}{'nC':>7}{'tol':>5}{'match':>7}{'random':>8}{'purity':>8}   (all R)      | R>3Rsun: match / random")
for thr in (4.5,5.0,5.5,6.0,7.0):
    PA,sa=peaks(SA,thr); PC,sc=peaks(SC,thr)
    PAw=(PA-C0)@M.T+T+C0; t=cKDTree(PC)
    for tol in (4.0,):
        d,i=t.query(PAw,distance_upper_bound=tol); ok=np.isfinite(d)
        rC=np.hypot(PC[i[ok],0]-CX,PC[i[ok],1]-CY)/RSUN
        f=0.;fo=0.
        for k in range(30):
            off=rng.uniform(-500,500,2); dd,ii=t.query(PAw+off,distance_upper_bound=tol)
            o2=np.isfinite(dd); f+=o2.sum()
            r2=np.hypot(PC[ii[o2],0]-CX,PC[ii[o2],1]-CY)/RSUN; fo+=(r2>3).sum()
        f/=30; fo/=30
        n_out=(rC>3).sum()
        print(f"{thr:5.1f}{len(PA):7d}{len(PC):7d}{tol:5.1f}{ok.sum():7d}{f:8.1f}{1-f/max(ok.sum(),1):8.2f}                | {n_out:5d} / {fo:5.1f}  purity={1-fo/max(n_out,1):.2f}")
