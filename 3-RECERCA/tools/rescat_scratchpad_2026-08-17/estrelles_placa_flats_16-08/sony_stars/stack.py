import numpy as np, pickle, sys
from scipy import ndimage
OFF=pickle.load(open("offsets2.pkl","rb"))['off']
EXP={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06988':1.0,
     'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
NUM=None
for n,e in EXP.items():
    num=np.load(f"num_{n}.npy"); den=np.load(f"den_{n}.npy")
    dx,dy=OFF[n]
    if abs(dx)+abs(dy)>0:
        num=ndimage.shift(num,(-dy,-dx),order=1,mode='constant',cval=0.0)
        den=ndimage.shift(den,(-dy,-dx),order=1,mode='constant',cval=0.0)
    if NUM is None: NUM=np.zeros_like(num); DEN=np.zeros_like(den); COV=np.zeros_like(den)
    NUM+=num*e; DEN+=den*(e*e); COV+=(den>0)*e
    print("stacked",n); sys.stdout.flush()
    del num,den
SNR=np.where(DEN>0,NUM/np.sqrt(np.maximum(DEN,1e-20)),0.0).astype(np.float32)
FLX=np.where(DEN>0,NUM/np.maximum(DEN,1e-20),0.0).astype(np.float32)   # ADU/s peak amplitude
np.save("SNR.npy",SNR); np.save("FLX.npy",FLX); np.save("DEN.npy",DEN.astype(np.float32)); np.save("COV.npy",COV.astype(np.float32))
m=DEN>0
q=np.percentile(SNR[m],[15.87,50,84.13,99.9])
print(f"stack SNR: med={q[1]:+.3f} sd=({q[1]-q[0]:.3f},{q[2]-q[1]:.3f}) p99.9={q[3]:.2f} max={SNR[m].max():.1f}")
print(f"full-depth area (all 8 frames, cov=25s): {(COV>24.5).sum()/1e6:.1f} Mpx of {m.sum()/1e6:.1f} Mpx")
lim=1.0/np.sqrt(np.median(DEN[COV>24.5]))
print(f"1-sigma peak-amplitude limit in the deepest area: {lim:.3f} ADU/s")
