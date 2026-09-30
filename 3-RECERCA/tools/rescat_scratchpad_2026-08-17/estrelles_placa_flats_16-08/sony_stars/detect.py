import numpy as np, pickle
from scipy import ndimage
SNR=np.load("SNR.npy"); FLX=np.load("FLX.npy"); DEN=np.load("DEN.npy"); COV=np.load("COV.npy")
moon=pickle.load(open("moon.pkl","rb"))
CX,CY=moon['DSC06993'][0],moon['DSC06993'][1]   # lunar centre in ref grid = Sun centre to ~2 px
RSUN=293.0
h,w=SNR.shape; Y,X=np.mgrid[0:h,0:w]
R=np.sqrt((X-CX)**2+(Y-CY)**2).astype(np.float32); del X,Y
np.save("R.npy",R)
lm=(SNR>6.0)&(SNR==ndimage.maximum_filter(SNR,11))&(COV>0)
ys,xs=np.nonzero(lm)
s=SNR[ys,xs]; r=R[ys,xs]
print(f"peaks SNR>6 : {len(xs)}")
for lo,hi in [(0,1.05),(1.05,1.5),(1.5,2),(2,3),(3,5),(5,8),(8,20)]:
    k=(r/RSUN>=lo)&(r/RSUN<hi)
    # area of that annulus inside the frame
    a=((R/RSUN>=lo)&(R/RSUN<hi)&(COV>0)).sum()
    print(f"  R/Rsun [{lo:4.2f},{hi:4.2f}): n={k.sum():5d}  area={a/1e6:6.2f} Mpx  density={k.sum()/max(a,1)*1e6:8.2f} /Mpx")
