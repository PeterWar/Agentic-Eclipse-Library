"""A10: la taca ampla (marca 7) als fotogrames RAW Vixen llargs: profunditat a la capa lunar de V69, i posició/profunditat fotograma a fotograma (i posició al SENSOR)."""
import sys, json, numpy as np, time
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.ndimage import map_coordinates, gaussian_filter, binary_fill_holes, label
from PIL import Image, ImageDraw
# 1) profunditat de la taca a la capa lunar (id 30) de V69
rgb,a=carrega(30); L=rgb.mean(-1)
m=np.load(SP+'/marques_218.npz'); M=np.zeros((2000,2000),np.float32); mx,my=int(m['x0'])-4377,int(m['y0'])-2777; M[my:my+m['A'].shape[0],mx:mx+m['A'].shape[1]]=m['A']/65535
R7=np.zeros((2000,2000),bool); R7[3896-2777:4137-2777,5224-4377:5447-4377]=M[3896-2777:4137-2777,5224-4377:5447-4377]>0.2
CXp,CYp=998.88,998.41; yy,xx=np.mgrid[0:2000,0:2000]; r=np.hypot(xx-CXp,yy-CYp)
yb,xb=np.nonzero(R7); rb=np.hypot(xb-CXp,yb-CYp); anell=(r>=rb.min()-10)&(r<=rb.max()+10)&(~R7)&(a>0.99)
Ls=gaussian_filter(L,8)
print('taca a la capa lunar V69: r %.0f–%.0f px del centre lunar, centre (%.0f,%.0f) abs'%(rb.min(),rb.max(),xb.mean()+4377,yb.mean()+2777))
print('  nivell mitjà dins la marca %.4f, a l\'anell del mateix radi (fora la marca) %.4f → profunditat %.1f %%'%(L[R7].mean(),L[anell].mean(),100*(1-L[R7].mean()/L[anell].mean())))
print('  amb suavitzat 8 px: mínim dins la marca %.4f (%.1f %% sota l\'anell)'%(Ls[R7].min(),100*(1-Ls[R7].min()/Ls[anell].mean())))
# 2) fotogrames RAW
import rawpy
ROOT='/Users/USUARI/Desktop/Eclipse 2026/0-RAW/Vixen R6III/Vixen Fase totalitat/'
frames=sys.argv[1:] or ['572A2983.CR3']
def llegeix(f):
    raw=rawpy.imread(ROOT+f); img=raw.postprocess(gamma=(1,1),no_auto_bright=True,output_bps=16,use_camera_wb=False,user_wb=[1,1,1,1],half_size=True,output_color=rawpy.ColorSpace.raw,demosaic_algorithm=rawpy.DemosaicAlgorithm.LINEAR)
    return img.astype(np.float32)
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
res=[]
for f in frames:
    t=time.time(); img=llegeix(f); Lum=img.mean(-1); cx,cy,R,rms=troba_lluna(Lum)
    esc=R/(456.0/2)   # escala sensor(half)/compost
    print(f'{f}: forma {Lum.shape} · Lluna centre sensor (half) ({cx:.1f},{cy:.1f}) R={R:.1f} px half → {2*R:.1f} full (compost 456) · rms {rms:.2f} · escala {esc:.4f} · %.1fs'%(time.time()-t),flush=True)
    # posició esperada de la taca (offset compost → sensor half, sense rotació): (−44.5,+234.5) → half /2 × esc
    bx,by=cx-44.5/2*esc,cy+234.5/2*esc
    # profunditat: mitjana en un disc de radi 45 px(half) vs anell del mateix radi lunar excloent ±35°
    yy,xx=np.mgrid[0:Lum.shape[0],0:Lum.shape[1]]; rr=np.hypot(xx-cx,yy-cy); az=np.rad2deg(np.arctan2(-(yy-cy),xx-cx))%360
    rt=np.hypot(bx-cx,by-cy); azt=np.rad2deg(np.arctan2(-(by-cy),bx-cx))%360
    dins=np.hypot(xx-bx,yy-by)<45; an=(np.abs(rr-rt)<45)&(np.abs(((az-azt+180)%360)-180)>35)&(rr<R*0.93)
    Ls=gaussian_filter(Lum,4)
    # mapa normalitzat del disc: Lum / (perfil radial mediana per anell) per veure la taca
    prof=np.array([np.median(Lum[(rr>=k)&(rr<k+4)]) for k in range(0,int(R*0.97),4)]); rad=np.interp(rr,np.arange(0,int(R*0.97),4)+2,prof)
    norm=np.where(rr<R*0.95,Ls/np.maximum(rad,1e-6),1)
    d=dict(frame=f,cx_half=round(float(cx),2),cy_half=round(float(cy),2),R_half=round(float(R),2),rms=round(rms,2),taca_xy_half=[round(float(bx),1),round(float(by),1)],
           nivell_taca=float(Lum[dins].mean()),nivell_anell=float(Lum[an].mean()),profunditat_pct=round(100*(1-Lum[dins].mean()/Lum[an].mean()),2),
           norm_taca=float(norm[dins].mean()),norm_min_taca=float(norm[dins].min()),norm_std_anell=float(norm[an].std()))
    res.append(d); print('   ',{k:v for k,v in d.items() if k!='frame'},flush=True)
    # vista: disc normalitzat (0,9–1,1) amb la posició esperada de la taca en cian
    x0,y0=int(cx-R*1.05),int(cy-R*1.05); S=int(R*2.1); crop=np.clip((norm[y0:y0+S,x0:x0+S]-0.9)/0.2,0,1)
    im=Image.fromarray(np.uint8(crop*255)).convert('RGB'); dr=ImageDraw.Draw(im); dr.ellipse([bx-x0-45,by-y0-45,bx-x0+45,by-y0+45],outline=(0,255,255),width=2); im.save(SP+f'/v_A10_{f[:-4]}_disc_norm.png')
json.dump(json.loads(json.dumps(res,default=float)),open(SP+'/a10_raw_'+('_'.join(x[:-4] for x in frames) if len(frames)<4 else 'lot')+'.json','w'),indent=1)
