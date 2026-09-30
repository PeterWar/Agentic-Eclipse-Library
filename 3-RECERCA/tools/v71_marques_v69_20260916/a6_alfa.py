"""A6: transparència residual del compost (el compost desat va aplanat sobre BLANC): on és, quant val, i coincideix amb les marques?"""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from PIL import Image, ImageDraw, ImageFont
C=np.load(SP+'/roi_compost.npz')['C']; a=C[...,3].astype(np.float32)/65535
Rr=np.load(SP+'/roi_recomp.npz'); ar=Rr['a'].astype(np.float32)/65535; Cr=Rr['C'].astype(np.float32)/65535
m=np.load(SP+'/marques_218.npz'); M=np.zeros((2000,2000),np.float32); mx,my=int(m['x0'])-4377,int(m['y0'])-2777; M[my:my+m['A'].shape[0],mx:mx+m['A'].shape[1]]=m['A']/65535
marques=json.load(open(SP+'/a1_marques.json'))
CX,CY=5377-4377-1.6,3777-2777-0.9; yy,xx=np.mgrid[0:2000,0:2000]; r=np.hypot(xx-CX,yy-CY); az=np.rad2deg(np.arctan2(-(yy-CY),xx-CX))%360
trans=a<0.998
print('píxels amb alfa<0,998 a la ROI:',int(trans.sum()),' alfa mínima:',a.min(),' (recomposició: %d, min %.3f)'%(int((ar<0.998).sum()),ar.min()))
print('recomposició sobre blanc vs compost desat: max |dif| DN16 = %.1f'%(np.abs((Cr*ar[...,None]+(1-ar[...,None]))-C[...,:3]/65535)[M==0].max()*65535))
# per anell de radi i per sector d'azimut (30°)
for lo,hi in [(0,400),(400,440),(440,450),(450,455),(455,460),(460,470),(470,520),(520,2000)]:
    k=(r>=lo)&(r<hi); print(f' r {lo:4d}–{hi:4d}: n_trans={int((trans&k).sum()):7d}  alfa min {a[k].min():.3f}  alfa mitjana on trans {a[trans&k].mean() if (trans&k).any() else 1:.3f}')
print('per sector (azimut antihorari des de l\'est; 90=dalt, 180=oest, 270=baix):')
for s in range(0,360,30):
    k=(az>=s)&(az<s+30)&(r>430)&(r<480); n=int((trans&k).sum()); print(f'  az {s:3d}–{s+30:3d}: n_trans={n:6d}  (1−alfa) màx {1-a[k].min():.3f}  mitjana on trans {(1-a[trans&k]).mean() if n else 0:.3f}')
# a cada marca: fracció de píxels de la marca (dilatada 3 px) amb transparència i (1−alfa) màx
from scipy.ndimage import binary_dilation
for q in marques:
    x0,y0,x1,y1=q['bbox']; sub=np.zeros_like(trans); sub[y0-2777:y1-2777,x0-4377:x1-4377]=M[y0-2777:y1-2777,x0-4377:x1-4377]>0; sub=binary_dilation(sub,iterations=4)
    print(f"marca {q['id']}: píxels {int(sub.sum())}, amb alfa<0,998: {int((sub&trans).sum())}, (1−alfa) màx {1-a[sub].min():.3f}, r de la marca {r[sub].min():.0f}–{r[sub].max():.0f}")
# vista: mapa de (1−alfa) ×20 amb les marques en cian
v=np.clip((1-a)*20,0,1); img=np.repeat(np.uint8(v*255)[...,None],3,-1); img[M>0]=[0,255,255]
Image.fromarray(img).save(SP+'/v_A6_transparencia_x20.png')
# zoom del limbe superior (marca 1): compost desat | recomposició sobre blanc | (1−alfa)×20
def g(x): return np.uint8(np.clip(x,0,1)**(1/2.2)*255)
x0,y0,x1,y1=5300-4377,3280-2777,5520-4377,3360-2777
pan=np.concatenate([g(C[y0:y1,x0:x1,:3]/65535),g(Cr[y0:y1,x0:x1]),np.repeat(np.uint8(v[y0:y1,x0:x1]*255)[...,None],3,-1)],0)
Image.fromarray(pan).resize((pan.shape[1]*4,pan.shape[0]*4),Image.Resampling.NEAREST).save(SP+'/v_A6_limbe_superior.png')
