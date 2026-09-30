import rawpy, numpy as np, pickle
from scipy import ndimage
from scipy.spatial import cKDTree
D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"; GAIN=3.323; RSUN=293.; AS=3.234
SA=np.load("SA.npy"); SC=np.load("SC.npy"); IA=np.load("IMGA.npy"); IC=np.load("IMGC.npy")
M=np.load("warpM.npy"); T=np.load("warpT.npy"); C0=np.load("warpC.npy")
OFF=pickle.load(open("offsets6.pkl","rb"))['off']; moon=pickle.load(open("moon.pkl","rb"))
CX,CY=moon['DSC06993'][0],moon['DSC06993'][1]
EXP={'DSC06984':2.,'DSC06985':1.,'DSC06987':8.,'DSC06991':1.,'DSC06993':8.,'DSC06996':2.,'DSC06999':2.}
GRP={'DSC06984':'A','DSC06985':'A','DSC06987':'A','DSC06991':'C','DSC06993':'C','DSC06996':'C','DSC06999':'C'}
def peaks(S,thr):
    lm=(S>thr)&(S==ndimage.maximum_filter(S,13)); lm[:45]=lm[-45:]=False; lm[:,:45]=lm[:,-45:]=False
    ys,xs=np.nonzero(lm)
    a=S[ys,xs-1];b=S[ys,xs];c=S[ys,xs+1];d=a-2*b+c; fx=np.where(d!=0,.5*(a-c)/np.where(d!=0,d,1),0)
    a=S[ys-1,xs];c=S[ys+1,xs];d=a-2*b+c; fy=np.where(d!=0,.5*(a-c)/np.where(d!=0,d,1),0)
    return np.c_[xs+np.clip(fx,-1,1),ys+np.clip(fy,-1,1)],b
PA,sa=peaks(SA,4.5); PC,sc=peaks(SC,4.5)
PAw=(PA-C0)@M.T+T+C0; tr=cKDTree(PC); d,i=tr.query(PAw,distance_upper_bound=4.0); ok=np.isfinite(d)
xa,ya=PA[ok,0],PA[ok,1]; xc,yc=PC[i[ok],0],PC[i[ok],1]; SNA=sa[ok]; SNC=sc[i[ok]]
N=len(xa); print("matched sources:",N)
def shape(IM,x,y,H=8):
    X0,Y0=int(round(x)),int(round(y))
    st=IM[Y0-H:Y0+H+1,X0-H:X0+H+1].astype(np.float64)
    if st.shape!=(2*H+1,2*H+1): return (np.nan,)*4
    Y,X=np.mgrid[-H:H+1,-H:H+1]; rr=np.hypot(X-(x-X0),Y-(y-Y0))
    st=st-np.median(st[(rr>5.5)&(rr<=H)])
    s=np.where((rr<=4.5)&(st>0),st,0); tot=s.sum()
    if tot<=0: return (np.nan,)*4
    mx=(s*X).sum()/tot; my=(s*Y).sum()/tot
    sxx=(s*(X-mx)**2).sum()/tot; syy=(s*(Y-my)**2).sum()/tot; sxy=(s*(X-mx)*(Y-my)).sum()/tot
    trr=sxx+syy; dd=np.sqrt(max((sxx-syy)**2+4*sxy**2,0))
    a=np.sqrt(max((trr+dd)/2,1e-9)); b=np.sqrt(max((trr-dd)/2,1e-9))
    return 2.3548*np.sqrt(max(trr/2,1e-9)), b/max(a,1e-9), np.degrees(.5*np.arctan2(2*sxy,sxx-syy)), tot
shA=np.array([shape(IA,x,y) for x,y in zip(xa,ya)]); shC=np.array([shape(IC,x,y) for x,y in zip(xc,yc)])
# per-frame photometry in the three Bayer channels
names=list(EXP); FL=np.zeros((N,len(names))); FE=np.zeros_like(FL); SN=np.zeros_like(FL)
CH=np.zeros((N,3)); CHn=np.zeros((N,3)); DK=np.zeros(N)
MD={e:np.load(f"masterdark_{int(e)}s.npy") for e in (1.,2.,8.)}
for jn,n in enumerate(names):
    e=EXP[n]; dx,dy=OFF[n]; bkg=np.load(f"bkg_{n}.npy"); md=MD[e]
    with rawpy.imread(D+n+".ARW") as rr:
        raw=rr.raw_image_visible.astype(np.float32); col=rr.raw_colors_visible
    res=raw-md-bkg; Nn=np.load(f"N_{n}.npy"); Dn=np.load(f"D_{n}.npy")
    S=np.where(Dn>0,Nn/np.sqrt(np.maximum(Dn,1e-30)),0.); del Nn,Dn
    px=(xa if GRP[n]=='A' else xc)+dx; py=(ya if GRP[n]=='A' else yc)+dy
    for q in range(N):
        X,Y=int(round(px[q])),int(round(py[q]))
        if not(11<X<raw.shape[1]-12 and 11<Y<raw.shape[0]-12): FL[q,jn]=np.nan; continue
        st=res[Y-10:Y+11,X-10:X+11]; cc=col[Y-10:Y+11,X-10:X+11]; dkm=(md-512)[Y-10:Y+11,X-10:X+11]
        Yg,Xg=np.mgrid[-10:11,-10:11]; rl=np.hypot(Xg-(px[q]-X),Yg-(py[q]-Y))
        for ci,sel in enumerate([(cc==0),((cc==1)|(cc==3)),(cc==2)]):
            ann=sel&(rl>7)&(rl<=10); ap=sel&(rl<=5)
            if ann.sum()<8 or ap.sum()<6: continue
            f=(st[ap]-np.median(st[ann])).sum()/e
            CH[q,ci]+=f*(4 if ci!=1 else 2); CHn[q,ci]+=1
        gsel=(cc==1)|(cc==3); ann=gsel&(rl>7)&(rl<=10); ap=gsel&(rl<=5)
        if ann.sum()<8: FL[q,jn]=np.nan; continue
        FL[q,jn]=(st[ap]-np.median(st[ann])).sum()*2./e
        FE[q,jn]=np.sqrt(ap.sum()*np.median(bkg[Y-10:Y+11,X-10:X+11])/GAIN)*2./e
        SN[q,jn]=S[Y-1:Y+2,X-1:X+2].max()
        DK[q]=max(DK[q],dkm[gsel&(rl<=2)].max() if (gsel&(rl<=2)).sum() else 0)
    del raw,res,bkg,S
    print("phot",n)
CH=CH/np.maximum(CHn,1)
ww=1/np.maximum(FE,1e-9)**2; good=np.isfinite(FL)
FT=np.nansum(np.where(good,FL*ww,0),1)/np.maximum(np.nansum(np.where(good,ww,0),1),1e-30)
ET=1/np.sqrt(np.maximum(np.nansum(np.where(good,ww,0),1),1e-30))
r=np.hypot(xc-CX,yc-CY)
np.savez("catalog.npz",xa=xa,ya=ya,xc=xc,yc=yc,SNA=SNA,SNC=SNC,shA=shA,shC=shC,FL=FL,FE=FE,SN=SN,
         FT=FT,ET=ET,r=r,CH=CH,DK=DK,names=np.array(names),CX=CX,CY=CY)
print("catalog saved:",N)
