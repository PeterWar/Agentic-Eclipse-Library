import numpy as np, pickle
from scipy import ndimage
from scipy.spatial import cKDTree
SA=np.load("SA.npy"); SC=np.load("SC.npy")
moon=pickle.load(open("moon.pkl","rb")); RSUN=293.
CX,CY=moon['DSC06993'][0],moon['DSC06993'][1]
h,w=SA.shape; yy,xx=np.mgrid[0:h,0:w]; R=np.hypot(xx-CX,yy-CY)/RSUN; del xx,yy
def peaks(S,thr):
    lm=(S>thr)&(S==ndimage.maximum_filter(S,15))&(R>3.0)
    ys,xs=np.nonzero(lm)
    a=S[ys,xs-1];b=S[ys,xs];c=S[ys,xs+1];d=a-2*b+c; fx=np.where(d!=0,.5*(a-c)/np.where(d!=0,d,1),0)
    a=S[ys-1,xs];c=S[ys+1,xs];d=a-2*b+c; fy=np.where(d!=0,.5*(a-c)/np.where(d!=0,d,1),0)
    return np.c_[xs+np.clip(fx,-1,1),ys+np.clip(fy,-1,1)],b
PA,sa=peaks(SA,7.0); PC,sc=peaks(SC,7.0)
t=cKDTree(PC); d,i=t.query(PA,distance_upper_bound=16.0)
ok=np.isfinite(d)
u=PA[ok]; v=PC[i[ok]]; s=np.minimum(sa[ok],sc[i[ok]])
o=np.argsort(-s)
print(f"high-SNR pairs (both stacks >7 sigma): {ok.sum()}")
print(f"{'xA':>8}{'yA':>8}{'snrA':>7}{'snrC':>7}{'dx':>7}{'dy':>7}")
for j in o[:35]:
    print(f"{u[j,0]:8.1f}{u[j,1]:8.1f}{sa[ok][j]:7.1f}{sc[i[ok]][j]:7.1f}{v[j,0]-u[j,0]:7.2f}{v[j,1]-u[j,1]:7.2f}")
np.save("u.npy",u); np.save("v.npy",v); np.save("s.npy",s)
