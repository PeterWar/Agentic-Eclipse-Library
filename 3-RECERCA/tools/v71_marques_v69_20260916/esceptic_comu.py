"""esceptic_comu: carregador RAW propi (negre 512 pla, mosaic RGBG, mida meitat), detector de Lluna, normalització per anells i mapatge al marc del compost."""
import numpy as np, rawpy, json
from scipy.ndimage import map_coordinates, gaussian_filter, label
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
ROOT='/Users/USUARI/Desktop/Eclipse 2026/0-RAW/Vixen R6III/Vixen Fase totalitat/'
CX,CY,RS=998.88,998.41,456.0   # centre físic i radi de la silueta al marc del compost (ROI 2000x2000)
TEXP={'572A2970':1/30,'572A2971':1/8,'572A2972':0.5,'572A2975':1/60,'572A2976':1/15,'572A2977':0.25,'572A2978':1.0,'572A2979':2.0,'572A2980':2.0,'572A2981':2.0,'572A2982':10.0,'572A2983':10.0,'572A2984':10.0,'572A2987':1/125,'572A2988':1/30,'572A2989':1/8,'572A2990':0.5,'572A2992':1/250,'572A2993':1/60,'572A2996':1.0,'572A3000':1/30,'572A3001':1/8,'572A3002':0.5,'572A3008':0.5}
def llegeix(frame, black=512.0):
    """Retorna dict amb Y (mitjana dels 4 plans Bayer), G, R, B (float32, mida meitat) i sat (algun pla ≥ 16000)."""
    raw=rawpy.imread(ROOT+frame+'.CR3'); m=raw.raw_image_visible.astype(np.float32)
    m=m[:m.shape[0]//2*2,:m.shape[1]//2*2]
    R=m[0::2,0::2]; G1=m[0::2,1::2]; G2=m[1::2,0::2]; B=m[1::2,1::2]
    sat=(R>=16000)|(G1>=16000)|(G2>=16000)|(B>=16000)
    R-=black; G1-=black; G2-=black; B-=black
    return dict(Y=(R+G1+G2+B)/4, G=(G1+G2)/2, R=R, B=B, sat=sat)
def troba_lluna(Lum):
    H,W=Lum.shape; wc=(slice(H//2-700,H//2+700),slice(W//2-700,W//2+700)); win=Lum[wc]; thr=0.4*np.percentile(win,99)
    lab,n=label(win<thr); best=None
    for k in range(1,n+1):
        m=lab==k; A=m.sum()
        if A<np.pi*150**2 or A>np.pi*300**2: continue
        ys,xs=np.nonzero(m); R0=np.sqrt(A/np.pi); circ=abs(xs.max()-xs.min()-2*R0)/(2*R0)
        if circ<0.15 and (best is None or A>best[0]): best=(A,xs.mean()+W//2-700,ys.mean()+H//2-700,R0)
    if best is None: raise RuntimeError('cap disc lunar trobat')
    _,cx,cy,R0=best
    TH=np.deg2rad(np.arange(0,360,0.5)); RR=np.arange(R0*0.8,R0*1.25,0.5)
    P=map_coordinates(Lum,[(cy-RR[None,:]*np.sin(TH[:,None])).ravel(),(cx+RR[None,:]*np.cos(TH[:,None])).ravel()],order=1).reshape(len(TH),len(RR))
    lo=np.median(P[:,RR<R0*0.9],1); hi=np.median(P[:,RR>R0*1.12],1); mid=(lo+hi)/2; rr=np.full(len(TH),np.nan)
    for i in range(len(TH)):
        j=np.nonzero(np.diff(np.sign(P[i]-mid[i]))!=0)[0]
        if len(j): k=j[0]; rr[i]=RR[k]+(mid[i]-P[i][k])/(P[i][k+1]-P[i][k]+1e-9)*0.5
    ok=np.isfinite(rr); A=np.stack([np.ones(ok.sum()),np.cos(TH[ok]),np.sin(TH[ok])],1); b=rr[ok]
    for _ in range(4):
        x,*_=np.linalg.lstsq(A,b,rcond=None); res=b-A@x; s=1.4826*np.median(np.abs(res)); w=np.abs(res)<3*max(s,.3); A,b=A[w],b[w]
    return cx+x[1],cy-x[2],x[0],float(np.std(b-A@x))
def perfil_radial(img,cx,cy,rmax,pas=3.0,mask=None):
    yy,xx=np.mgrid[0:img.shape[0],0:img.shape[1]]; rr=np.hypot(xx-cx,yy-cy)
    edges=np.arange(0,rmax+pas,pas); prof=[]
    for k in range(len(edges)-1):
        s=(rr>=edges[k])&(rr<edges[k+1])
        if mask is not None: s&=mask
        prof.append(np.nanmedian(img[s]) if s.any() else np.nan)
    return edges[:-1]+pas/2, np.array(prof), rr
def norm_anells(img,cx,cy,R,rlim=0.97,mask=None):
    """img / perfil radial (mediana per anells de 3 px) dins r<rlim·R; fora NaN."""
    rc,prof,rr=perfil_radial(img,cx,cy,R*rlim+3,3.0,mask)
    ok=np.isfinite(prof); rad=np.interp(rr,rc[ok],prof[ok])
    return np.where(rr<R*rlim,img/np.maximum(rad,1e-6),np.nan)
def cap_al_compost(img,cx,cy,R,phi_deg,mida=2000,order=1,cval=np.nan):
    """Remostreja img (marc RAW meitat, Lluna a cx,cy radi R) al marc del compost 2000x2000 (centre CX,CY radi RS) amb gir phi."""
    Y,X=np.mgrid[0:mida,0:mida]; dx=X-CX; dy=Y-CY; s=R/RS; p=np.deg2rad(phi_deg)
    xr=cx+s*(dx*np.cos(p)-dy*np.sin(p)); yr=cy+s*(dx*np.sin(p)+dy*np.cos(p))
    return map_coordinates(np.nan_to_num(img,nan=0.0),[yr,xr],order=order,cval=cval)
def del_compost_al_raw(X,Y,cx,cy,R,phi_deg):
    dx=X-CX; dy=Y-CY; s=R/RS; p=np.deg2rad(phi_deg)
    return cx+s*(dx*np.cos(p)-dy*np.sin(p)), cy+s*(dx*np.sin(p)+dy*np.cos(p))
def graella():
    yy,xx=np.mgrid[0:2000,0:2000]; rr=np.hypot(xx-CX,yy-CY)/RS; az=np.rad2deg(np.arctan2(-(yy-CY),xx-CX))%360
    return rr,az
def marca7():
    m=np.load(SP+'/marques_218.npz'); M=np.zeros((2000,2000),np.float32); mx,my=int(m['x0'])-4377,int(m['y0'])-2777
    M[my:my+m['A'].shape[0],mx:mx+m['A'].shape[1]]=m['A']/65535
    R7=np.zeros((2000,2000),bool); R7[3896-2777:4137-2777,5224-4377:5447-4377]=M[3896-2777:4137-2777,5224-4377:5447-4377]>0.2
    return R7
def profunditat_taca(mapa,R7,rr,az,exclou_deg=35,az0=259.0):
    """mitjana dins la marca 7 vs anell del mateix radi fora (excloent ±exclou° d'azimut). Retorna % (positiu = més fosc)."""
    rb=rr[R7]; an=(rr>=rb.min()-10/RS)&(rr<=rb.max()+10/RS)&(~R7)&(np.abs(((az-az0+180)%360)-180)>exclou_deg)&np.isfinite(mapa)
    return 100*(1-np.nanmean(mapa[R7])/np.nanmean(mapa[an]))
def pearson(a,b,k):
    a=a[k]; b=b[k]; g=np.isfinite(a)&np.isfinite(b); return float(np.corrcoef(a[g],b[g])[0,1])
def xcorr_pic(a,b,maxs=20):
    """correlació creuada normalitzada per FFT de dos mapes (mateix tamany, ja emmascarats a 0 fora); retorna (dx,dy,cmax,c0)."""
    a=a-a.mean(); b=b-b.mean(); A=np.fft.rfft2(a); B=np.fft.rfft2(b); cc=np.fft.irfft2(A*np.conj(B),s=a.shape); cc=np.fft.fftshift(cc)/(np.sqrt((a**2).sum()*(b**2).sum())+1e-12)
    c=np.array(cc.shape)//2; win=cc[c[0]-maxs:c[0]+maxs+1,c[1]-maxs:c[1]+maxs+1]; iy,ix=np.unravel_index(win.argmax(),win.shape)
    return int(ix-maxs),int(iy-maxs),float(win.max()),float(cc[c[0],c[1]])
