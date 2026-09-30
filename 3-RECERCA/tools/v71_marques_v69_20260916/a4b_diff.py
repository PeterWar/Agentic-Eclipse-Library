"""A4b: on difereix la recomposició del compost desat? mapa i sondes per capa."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from PIL import Image
C=np.load(SP+'/roi_compost.npz')['C'].astype(np.float32)/65535
Rr=np.load(SP+'/roi_recomp.npz'); Cr=Rr['C'].astype(np.float32)/65535
m=np.load(SP+'/marques_218.npz'); A=np.zeros((2000,2000),np.float32); mx,my=int(m['x0'])-4377,int(m['y0'])-2777; A[my:my+m['A'].shape[0],mx:mx+m['A'].shape[1]]=m['A']/65535
d=(np.abs(Cr-C[...,:3]).max(-1)*65535); d[A>0]=0
img=np.clip(d/400,0,1); Image.fromarray(np.uint8(img*255)).save(SP+'/v_A4b_diff.png')
# retall 1:1 del limbe oest (x 4880–5080, y 3600–3900) ×3: compost desat | recomposició | dif
def srgbish(a): return np.uint8(np.clip(a,0,1)**(1/2.2)*255)
x0,y0,x1,y1=4880-4377,3600-2777,5080-4377,3900-2777
pan=np.concatenate([srgbish(C[y0:y1,x0:x1,:3]),srgbish(Cr[y0:y1,x0:x1]),np.repeat(np.uint8(np.clip(d[y0:y1,x0:x1]/400,0,1)*255)[...,None],3,-1)],1)
Image.fromarray(pan).resize((pan.shape[1]*3,pan.shape[0]*3),Image.Resampling.NEAREST).save(SP+'/v_A4b_oest.png')
# sondes: els 8 píxels amb més diferència
yy,xx=np.unravel_index(np.argsort(d.ravel())[::-1][:2000],d.shape)
seq=[l for l in IDX['layers'] if l['visible'] and l['id']!=218]
caps={l['id']:carrega(l['id']) for l in seq}
for k in [0,250,500,1000,1999]:
    y,x=yy[k],xx[k]; print(f"\n({x+4377},{y+2777}) dif {d[y,x]:.0f} DN16  compost RGB={np.round(C[y,x,:3]*65535).astype(int)} a={C[y,x,3]:.3f} | recomp={np.round(Cr[y,x]*65535).astype(int)}")
    for l in seq:
        rgb,a=caps[l['id']]
        if a[y,x]>0.001: print(f"   id {l['id']:>3} {l['blend']:12s} a_ef={a[y,x]:.3f} rgb={np.round(rgb[y,x]*65535).astype(int)}  {l['name'][:28]}")
