import numpy as np, pickle
from scipy import ndimage
SNR=np.load("SNR.npy"); FLX=np.load("FLX.npy"); DEN=np.load("DEN.npy"); COV=np.load("COV.npy"); IMG=np.load("IMG.npy")
OFF=pickle.load(open("offsets3.pkl","rb"))['off']
moon=pickle.load(open("moon.pkl","rb"))
EXP={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06988':1.0,
     'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
GRP={'DSC06984':'A','DSC06985':'A','DSC06987':'A','DSC06988':'B',
     'DSC06991':'C','DSC06993':'C','DSC06996':'C','DSC06999':'C'}
CX,CY=moon['DSC06993'][0],moon['DSC06993'][1]; RSUN=293.0
h,w=SNR.shape
lm=(SNR>5.5)&(SNR==ndimage.maximum_filter(SNR,13))&(COV>0)
ys,xs=np.nonzero(lm); print("raw stack peaks >5.5 sigma:",len(xs))
r=np.sqrt((xs-CX)**2+(ys-CY)**2)/RSUN
# --- shape from the stacked image: 2nd moments in a 13x13 box, local-median removed
def shape(x,y,H=6):
    st=IMG[y-H:y+H+1,x-H:x+H+1].astype(np.float64)
    if st.shape!=(2*H+1,2*H+1): return (np.nan,)*5
    ring=np.ones_like(st,bool); Y,X=np.mgrid[-H:H+1,-H:H+1]
    rr=np.hypot(X,Y); ring=(rr>4.5)
    st=st-np.median(st[ring])
    core=rr<=4.0
    s=st*core; s=np.where(s>0,s,0)
    tot=s.sum()
    if tot<=0: return (np.nan,)*5
    mx=(s*X).sum()/tot; my=(s*Y).sum()/tot
    sxx=(s*(X-mx)**2).sum()/tot; syy=(s*(Y-my)**2).sum()/tot; sxy=(s*(X-mx)*(Y-my)).sum()/tot
    tr=sxx+syy; dd=np.sqrt(max((sxx-syy)**2+4*sxy**2,0))
    a=np.sqrt(max((tr+dd)/2,1e-9)); b=np.sqrt(max((tr-dd)/2,1e-9))
    ang=np.degrees(0.5*np.arctan2(2*sxy,sxx-syy))
    fwhm=2.3548*np.sqrt(max(tr/2,1e-9))
    return fwhm,a,b,ang,b/max(a,1e-9)
SH=np.array([shape(int(x),int(y)) for x,y in zip(xs,ys)])
# --- per frame / per group
names=sorted(EXP); per={}
for n in names:
    N=np.load(f"N_{n}.npy"); Dn=np.load(f"D_{n}.npy"); dx,dy=OFF[n]
    sx=np.round(xs+dx).astype(int); sy=np.round(ys+dy).astype(int)
    ok=(sx>3)&(sx<w-4)&(sy>3)&(sy<h-4)
    nn=np.zeros(len(xs)); dd=np.zeros(len(xs))
    idx=np.nonzero(ok)[0]
    for i in idx:
        a=N[sy[i]-1:sy[i]+2,sx[i]-1:sx[i]+2]; b=Dn[sy[i]-1:sy[i]+2,sx[i]-1:sx[i]+2]
        s=np.where(b>0,a/np.sqrt(np.maximum(b,1e-30)),0); j=np.unravel_index(np.argmax(s),s.shape)
        nn[i]=a[j]; dd[i]=b[j]
    per[n]=dict(N=nn,D=dd,ok=ok,sx=sx,sy=sy,
                snr=np.where(dd>0,nn/np.sqrt(np.maximum(dd,1e-30)),0))
    del N,Dn
def comb(sel):
    A=np.zeros(len(xs)); B=np.zeros(len(xs))
    for n in sel: A+=per[n]['N']*EXP[n]*per[n]['ok']; B+=per[n]['D']*EXP[n]**2*per[n]['ok']
    return np.where(B>0,A/np.sqrt(np.maximum(B,1e-30)),0), np.where(B>0,A/np.maximum(B,1e-30),0)
gA=[n for n in names if GRP[n]=='A']; gC=[n for n in names if GRP[n]=='C']; gB=['DSC06988']
sA,fA=comb(gA); sC,fC=comb(gC); sB,fB=comb(gB)
nd=sum(((per[n]['snr']>3.0)&per[n]['ok']).astype(int) for n in names)
pickle.dump(dict(xs=xs,ys=ys,snr=SNR[ys,xs],flx=FLX[ys,xs],r=r,SH=SH,sA=sA,sC=sC,sB=sB,
                 fA=fA,fC=fC,nd=nd,per=per,CX=CX,CY=CY),open("final.pkl","wb"))
good=(sA>3.0)&(sC>3.0)&(SH[:,0]>1.4)&(SH[:,0]<6.0)&(SH[:,4]>0.45)
print(f"pass both groups + PSF-like shape: {good.sum()}")
o=np.argsort(-SNR[ys,xs])
print(f"\n{'x':>6}{'y':>6}{'R/Rs':>6}{'stack':>7}{'A':>7}{'B':>7}{'C':>7}{'nfr':>4}{'FWHM':>6}{'b/a':>6}{'ang':>6}{'flx':>9}  ok")
for i in o:
    if SNR[ys[i],xs[i]]<6.0: break
    print(f"{xs[i]:6d}{ys[i]:6d}{r[i]:6.2f}{SNR[ys[i],xs[i]]:7.1f}{sA[i]:7.1f}{sB[i]:7.1f}{sC[i]:7.1f}{nd[i]:4d}"
          f"{SH[i,0]:6.2f}{SH[i,4]:6.2f}{SH[i,3]:6.0f}{FLX[ys[i],xs[i]]:9.1f}  {'YES' if good[i] else '-'}")
