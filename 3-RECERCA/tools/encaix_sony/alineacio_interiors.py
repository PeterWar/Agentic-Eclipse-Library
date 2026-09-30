import numpy as np, os
from scipy import ndimage as ndi
from psd_tools import PSDImage
def disp(a,b,s=6):
    A=a-ndi.gaussian_filter(a,s); B=b-ndi.gaussian_filter(b,s); A/=(A.std()+1e-9); B/=(B.std()+1e-9)
    F=np.fft.fft2(A)*np.conj(np.fft.fft2(B)); F/=np.abs(F)+1e-9; pc=np.real(np.fft.ifft2(F))
    iy,ix=np.unravel_index(np.argmax(pc),pc.shape); dy=iy if iy<=pc.shape[0]//2 else iy-pc.shape[0]; dx=ix if ix<=pc.shape[1]//2 else ix-pc.shape[1]
    ys,xs=np.mgrid[-1:2,-1:2]; w=np.array([[pc[(iy+i)%pc.shape[0],(ix+j)%pc.shape[1]] for j in (-1,0,1)] for i in (-1,0,1)]); w=np.clip(w-w.min(),0,None)
    return -(dx+(w*xs).sum()/w.sum()), -(dy+(w*ys).sum()/w.sum()), pc.max()
D=os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
I=PSDImage.open(D+'CapesInteriors.psb'); layers=list(I)
C={}
for l in layers:
    a=l.numpy(); C[l.name]=(a[...,:3].mean(-1).astype(np.float32), l.bbox); print('llegida', l.name, l.bbox, flush=True)
def patch(name,x0,y0,S):
    Cc,b=C[name]; lx0,ly0,lx1,ly1=b; out=np.full((S,S),np.nan,np.float32)
    ix0,iy0,ix1,iy1=max(x0,lx0),max(y0,ly0),min(x0+S,lx1),min(y0+S,ly1)
    out[iy0-y0:iy1-y0, ix0-x0:ix1-x0]=Cc[iy0-ly0:iy1-ly0, ix0-lx0:ix1-lx0]; return out
sun=(3564.9,2275.7); RS=446.15
def ring(nA,nB,rr,S,thr=0.1,mask_disc=True):
    res=[]
    for ang in range(0,360,30):
        cx=sun[0]+rr*RS*np.cos(np.radians(ang)); cy=sun[1]-rr*RS*np.sin(np.radians(ang)); x0=int(cx-S/2); y0=int(cy-S/2)
        a=patch(nA,x0,y0,S); b=patch(nB,x0,y0,S)
        if np.isnan(a).any() or np.isnan(b).any(): continue
        if mask_disc:
            yy,xx=np.mgrid[y0:y0+S,x0:x0+S]; rr_=np.hypot(xx-sun[0],yy-sun[1])/RS; m=(rr_>1.06).astype(np.float32)
            a=a*m+np.nanmedian(a)*(1-m); b=b*m+np.nanmedian(b)*(1-m)
        res.append(disp(a,b))
    good=[r for r in res if r[2]>thr]
    print(f'  {nB[:22]:22s} respecte de {nA[:22]:22s} r={rr} S={S}: pics>{thr}: {len(good)}/{len(res)}; ' + (f'mediana ({np.median([g[0] for g in good]):+.2f},{np.median([g[1] for g in good]):+.2f}) px, pic màx {max(g[2] for g in good):.2f}' if good else 'cap pic fiable') + '  [' + ' '.join(f'({r[0]:+.1f},{r[1]:+.1f}|{r[2]:.2f})' for r in res) + ']', flush=True)
N={l.name[:2]:l.name for l in layers}
print('== CapesInteriors: cada capa contra la veïna (i contra Capa 1 = TIFF), coordenades de document; positiu = la segona més a la dreta/avall')
ring(N['03'],'Capa 1',1.6,768); ring(N['04'],N['03'],1.35,512); ring(N['05'],N['04'],1.25,512); ring(N['06'],N['05'],1.2,512); ring(N['07'],N['06'],1.15,384)
ring(N['08'],N['07'],1.12,384); ring(N['09'],N['08'],1.1,384); ring(N['10'],N['09'],1.08,384); ring(N['11'],N['10'],1.06,384); ring(N['12'],N['11'],1.05,384)
ring('Capa 1',N['05'],1.25,512); ring('Capa 1',N['06'],1.2,512); ring('Capa 1',N['07'],1.15,384)
