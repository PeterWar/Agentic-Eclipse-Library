import rawpy, numpy as np, pickle
from scipy import ndimage
D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
SNR=np.load("F_SNR.npy"); DEN=np.load("F_DEN.npy"); COV=np.load("F_COV.npy"); IMG=np.load("F_IMG.npy")
OFF=pickle.load(open("offsets6.pkl","rb"))['off']; moon=pickle.load(open("moon.pkl","rb"))
USE={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
GRP={'DSC06984':'A','DSC06985':'A','DSC06987':'A','DSC06991':'C','DSC06993':'C','DSC06996':'C','DSC06999':'C'}
CX,CY=moon['DSC06993'][0],moon['DSC06993'][1]; RSUN=293.0; SCALE=3.234
h,w=SNR.shape
lm=(SNR>5.0)&(SNR==ndimage.maximum_filter(SNR,15))&(COV>0)
ys,xs=np.nonzero(lm); r=np.hypot(xs-CX,ys-CY)
print("stack peaks >5 sigma:",len(xs))
# centroid + shape + FWHM on the stacked image
def meas(x,y,H=8):
    st=IMG[y-H:y+H+1,x-H:x+H+1].astype(np.float64)
    if st.shape!=(2*H+1,2*H+1): return None
    Y,X=np.mgrid[-H:H+1,-H:H+1]; rr=np.hypot(X,Y)
    st=st-np.median(st[(rr>5.5)&(rr<=H)])
    c=rr<=4.5; s=np.where(st*c>0,st*c,0); tot=s.sum()
    if tot<=0: return None
    mx=(s*X).sum()/tot; my=(s*Y).sum()/tot
    sxx=(s*(X-mx)**2).sum()/tot; syy=(s*(Y-my)**2).sum()/tot; sxy=(s*(X-mx)*(Y-my)).sum()/tot
    tr=sxx+syy; dd=np.sqrt(max((sxx-syy)**2+4*sxy**2,0))
    a=np.sqrt(max((tr+dd)/2,1e-9)); b=np.sqrt(max((tr-dd)/2,1e-9))
    return x+mx,y+my,2.3548*np.sqrt(max(tr/2,1e-9)),b/max(a,1e-9),np.degrees(0.5*np.arctan2(2*sxy,sxx-syy))
M=[meas(int(x),int(y)) for x,y in zip(xs,ys)]
ok=np.array([m is not None for m in M])
cx=np.array([m[0] if m else np.nan for m in M]); cy=np.array([m[1] if m else np.nan for m in M])
fw=np.array([m[2] if m else np.nan for m in M]); ba=np.array([m[3] if m else np.nan for m in M])
ang=np.array([m[4] if m else np.nan for m in M])
# per-frame photometry on the raw green pixels + hot-pixel check
names=list(USE); per={n:{} for n in names}
MD={e:np.load(f"masterdark_{int(e)}s.npy") for e in (1.,2.,8.)}
FL=np.zeros((len(xs),len(names))); FE=np.zeros_like(FL); SN=np.zeros_like(FL); DK=np.zeros_like(FL)
for jn,n in enumerate(names):
    e=USE[n]; dx,dy=OFF[n]; bkg=np.load(f"bkg_{n}.npy"); md=MD[e]
    with rawpy.imread(D+n+".ARW") as rr:
        raw=rr.raw_image_visible.astype(np.float32); col=rr.raw_colors_visible
    g=((col==1)|(col==3)); res=raw-md-bkg
    N=np.load(f"N_{n}.npy"); Dn=np.load(f"D_{n}.npy")
    S=np.where(Dn>0,N/np.sqrt(np.maximum(Dn,1e-30)),0.)
    for i in range(len(xs)):
        if not np.isfinite(cx[i]): FL[i,jn]=np.nan; continue
        X=int(round(cx[i]+dx)); Y=int(round(cy[i]+dy))
        if not(9<X<w-10 and 9<Y<h-10): FL[i,jn]=np.nan; continue
        st=res[Y-9:Y+10,X-9:X+10]; gg=g[Y-9:Y+10,X-9:X+10]; dd=(md-512)[Y-9:Y+10,X-9:X+10]
        Yg,Xg=np.mgrid[-9:10,-9:10]; rl=np.hypot(Xg-(cx[i]+dx-X),Yg-(cy[i]+dy-Y))
        ann=gg&(rl>7)&(rl<=9); ap=gg&(rl<=5)
        if ann.sum()<10 or ap.sum()<10: FL[i,jn]=np.nan; continue
        b0=np.median(st[ann])
        FL[i,jn]=(st[ap]-b0).sum()*2.0/e
        FE[i,jn]=np.sqrt(ap.sum()*np.median(bkg[Y-9:Y+10,X-9:X+10])/3.323)*2.0/e
        SN[i,jn]=S[max(Y-1,0):Y+2,max(X-1,0):X+2].max()
        DK[i,jn]=dd[gg&(rl<=2)].max() if (gg&(rl<=2)).sum() else 0
    del raw,res,bkg,N,Dn,S
    print("photometry",n)
gA=[i for i,n in enumerate(names) if GRP[n]=='A']; gC=[i for i,n in enumerate(names) if GRP[n]=='C']
def cg(idx):
    f=FL[:,idx]; s=FE[:,idx]; ww=1/np.maximum(s,1e-9)**2
    good=np.isfinite(f)
    F=np.nansum(np.where(good,f*ww,0),1)/np.maximum(np.nansum(np.where(good,ww,0),1),1e-30)
    E=1/np.sqrt(np.maximum(np.nansum(np.where(good,ww,0),1),1e-30))
    return F,E
FA,EA=cg(gA); FC,EC=cg(gC); FT,ET=cg(list(range(len(names))))
nd=np.nansum(SN>3.0,axis=1)
np.savez("meas.npz",xs=xs,ys=ys,cx=cx,cy=cy,r=r,snr=SNR[ys,xs],fw=fw,ba=ba,ang=ang,
         FL=FL,FE=FE,SN=SN,DK=DK,FA=FA,EA=EA,FC=FC,EC=EC,FT=FT,ET=ET,nd=nd,names=np.array(names),CX=CX,CY=CY)
print("saved")
