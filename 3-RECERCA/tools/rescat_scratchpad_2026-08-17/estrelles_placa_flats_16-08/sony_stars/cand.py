import numpy as np, pickle
from scipy import ndimage
SNR=np.load("SNR.npy"); DEN=np.load("DEN.npy"); COV=np.load("COV.npy"); R=np.load("R.npy")
OFF=pickle.load(open("offsets2.pkl","rb"))['off']
EXP={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06988':1.0,
     'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
GRP={'DSC06984':'A','DSC06985':'A','DSC06987':'A','DSC06988':'B',
     'DSC06991':'C','DSC06993':'C','DSC06996':'C','DSC06999':'C'}
RSUN=293.0
lm=(SNR>5.5)&(SNR==ndimage.maximum_filter(SNR,11))&(COV>0)&(R>2.5*RSUN)
ys,xs=np.nonzero(lm)
print("candidates R>2.5Rsun, stack SNR>5.5 :",len(xs))
names=sorted(EXP)
NUMv={}; DENv={}
per={}
for n in names:
    num=np.load(f"num_{n}.npy"); den=np.load(f"den_{n}.npy"); e=EXP[n]
    dx,dy=OFF[n]
    sx=np.round(xs+dx).astype(int); sy=np.round(ys+dy).astype(int)
    ok=(sx>2)&(sx<num.shape[1]-3)&(sy>2)&(sy<num.shape[0]-3)
    nb=np.zeros(len(xs)); db=np.zeros(len(xs)); sn=np.zeros(len(xs))
    for i in np.nonzero(ok)[0]:
        wn=num[sy[i]-2:sy[i]+3,sx[i]-2:sx[i]+3]; wd=den[sy[i]-2:sy[i]+3,sx[i]-2:sx[i]+3]
        ss=np.where(wd>0,wn/np.sqrt(np.maximum(wd,1e-20)),0.0)
        j=np.unravel_index(np.argmax(ss),ss.shape)
        nb[i]=wn[j]; db[i]=wd[j]; sn[i]=ss[j]
    per[n]=dict(num=nb,den=db,snr=sn,ok=ok,sx=sx,sy=sy)
    print("  sampled",n)
    del num,den
def combine(sel):
    N=np.zeros(len(xs)); D=np.zeros(len(xs))
    for n in sel:
        e=EXP[n]; N+=per[n]['num']*e*per[n]['ok']; D+=per[n]['den']*e*e*per[n]['ok']
    return np.where(D>0,N/np.sqrt(np.maximum(D,1e-20)),0.0), np.where(D>0,N/np.maximum(D,1e-20),0.0)
A=[n for n in names if GRP[n]=='A']; B=[n for n in names if GRP[n]=='B']; C=[n for n in names if GRP[n]=='C']
snrA,fA=combine(A); snrB,fB=combine(B); snrC,fC=combine(C)
ndet=sum((per[n]['snr']>3.5)&per[n]['ok'] for n in names)
pickle.dump(dict(xs=xs,ys=ys,snr=SNR[ys,xs],r=R[ys,xs],snrA=snrA,snrC=snrC,snrB=snrB,
                 fA=fA,fC=fC,ndet=ndet,per=per,names=names),open("cand.pkl","wb"))
real=(snrA>3.5)&(snrC>3.5)
print(f"\nboth groups A and C at >3.5 sigma : {real.sum()}")
print(f"only A: {((snrA>3.5)&(snrC<=3.5)).sum()}   only C: {((snrC>3.5)&(snrA<=3.5)).sum()}   neither: {((snrA<=3.5)&(snrC<=3.5)).sum()}")
o=np.argsort(-SNR[ys,xs])
print(f"\n{'x':>6}{'y':>6}{'R/Rs':>7}{'stack':>8}{'grpA':>8}{'grpC':>8}{'grpB':>7}{'nfr':>5}")
for i in o[:45]:
    print(f"{xs[i]:6d}{ys[i]:6d}{R[ys[i],xs[i]]/RSUN:7.2f}{SNR[ys[i],xs[i]]:8.1f}{snrA[i]:8.1f}{snrC[i]:8.1f}{snrB[i]:7.1f}{ndet[i]:5d}")
