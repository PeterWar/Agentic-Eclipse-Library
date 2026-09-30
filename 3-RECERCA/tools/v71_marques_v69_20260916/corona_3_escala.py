"""CORONA pas 3: (a) radi del limbe als fotogrames curts (troba_lluna + màxim de gradient radial); (b) correlació creuada per FFT HDR↔compost per escala amb desplaçament lliure."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.ndimage import map_coordinates, gaussian_filter, label
exec(open(SP+'/a10_lluna_raw.py').read().split('res=[]')[0].split('# 2) fotogrames RAW')[1])
from corona_raw import llegeix_ma
out={}
def limbe_gradient(Lum,cx,cy,R0,sat):
    TH=np.deg2rad(np.arange(0,360,0.5)); RR=np.arange(R0-12,R0+12,0.25)
    xs=cx+RR[None,:]*np.cos(TH[:,None]); ys=cy-RR[None,:]*np.sin(TH[:,None])
    P=map_coordinates(Lum,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(RR)); Sm=map_coordinates(sat.astype(np.float32),[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(RR))
    g=np.gradient(gaussian_filter(P,(0,2)),axis=1); rr=np.full(len(TH),np.nan)
    for i in range(len(TH)):
        if Sm[i].max()>0: continue   # azimut amb saturació al voltant del limbe: fora
        k=np.argmax(g[i]); 
        if 2<k<len(RR)-3: rr[i]=RR[k]
    ok=np.isfinite(rr); A=np.stack([np.ones(ok.sum()),np.cos(TH[ok]),np.sin(TH[ok])],1); b=rr[ok]
    for _ in range(4):
        x,*_=np.linalg.lstsq(A,b,rcond=None); res=b-A@x; s=1.4826*np.median(np.abs(res)); w=np.abs(res)<3*max(s,.3); A,b=A[w],b[w]
    return float(x[0]),float(cx+x[1]),float(cy-x[2]),int(ok.sum()),float(np.std(b-A@x))
for f in ['572A2970.CR3','572A2971.CR3','572A2972.CR3','572A2979.CR3']:
    img,sat=llegeix_ma(f); Lum=img.mean(-1)
    try: cx,cy,R,rms=troba_lluna(Lum); d=dict(troba_lluna=[round(float(cx),2),round(float(cy),2),round(float(R),2),round(rms,2)])
    except Exception as e: d=dict(troba_lluna=str(e)); cx,cy,R=1789.0,1136.3,225.7
    Rg,cxg,cyg,n,rmsg=limbe_gradient(Lum,cx,cy,R,sat); d['gradient']=[round(Rg,2),round(cxg,2),round(cyg,2),n,round(rmsg,2)]
    out[f]=d; print(f,d,flush=True)
# (b) correlació creuada FFT: HDR projectat (log, passa-alt 3–25) vs compost (passa-alt 3–25), anell 480–950, escales 2.00–2.07
D=np.load(SP+'/corona_hdr_sensor_half.npz'); HDR=D['hdr']; VAL=D['valid']; cx,cy=float(D['cx']),float(D['cy'])
Rc=np.load(SP+'/roi_recomp.npz'); Lc=Rc['C'].astype(np.float32).mean(-1)/65535; CXp,CYp=998.88,998.41
yy,xx=np.mgrid[0:2000,0:2000]; rp=np.hypot(xx-CXp,yy-CYp); anell=(rp>480)&(rp<950)
hp=lambda a,s1,s2: gaussian_filter(a,s1)-gaussian_filter(a,s2)
def projecta(img,esc,ang,cxo,cyo,H,W,order=1):
    yy,xx=np.mgrid[0:H,0:W].astype(np.float64); X=xx-cxo; Y=yy-cyo; t=np.deg2rad(ang)
    x=X*np.cos(t)-Y*np.sin(t); y=X*np.sin(t)+Y*np.cos(t); return map_coordinates(img,[cy+y/esc,cx+x/esc],order=order,mode='constant',cval=0.0)
def xcorr(A,B,m,dmax=25):
    A=np.where(m,A-A[m].mean(),0); B=np.where(m,B-B[m].mean(),0); A/=np.sqrt((A**2).sum()); B/=np.sqrt((B**2).sum())
    c=np.fft.irfft2(np.fft.rfft2(A)*np.conj(np.fft.rfft2(B)),s=A.shape); c=np.fft.fftshift(c); c0=np.array(c.shape)//2
    w=c[c0[0]-dmax:c0[0]+dmax+1,c0[1]-dmax:c0[1]+dmax+1]; k=np.unravel_index(np.argmax(w),w.shape)
    return float(w.max()),int(k[1]-dmax),int(k[0]-dmax),float(c[c0[0],c0[1]])
Hc=hp(Lc,3,25); res=[]
for ang in (11.0,):
    for esc in np.arange(2.000,2.0701,0.005):
        P=projecta(HDR,esc,ang,CXp,CYp,2000,2000); V=projecta(VAL.astype(np.float32),esc,ang,CXp,CYp,2000,2000)>0.999
        Hh=hp(np.log10(np.maximum(P,1)),3,25); m=anell&V; cmax,dx,dy,c0=xcorr(Hh,Hc,m)
        # també per bandes radials, per veure si el desplaçament òptim creix amb r (= error d'escala)
        bandes=[]
        for r0,r1 in ((480,600),(600,750),(750,950)):
            mm=m&(rp>=r0)&(rp<r1); cb,bx,by,_=xcorr(Hh,Hc,mm); bandes.append([r0,r1,round(cb,4),bx,by])
        res.append(dict(ang=ang,esc=round(float(esc),3),corr_max=round(cmax,4),desplac=[dx,dy],corr_0=round(c0,4),bandes=bandes)); print(res[-1],flush=True)
out['xcorr']=res; json.dump(out,open(SP+'/corona_3_escala.json','w'),indent=1); print('fet')
