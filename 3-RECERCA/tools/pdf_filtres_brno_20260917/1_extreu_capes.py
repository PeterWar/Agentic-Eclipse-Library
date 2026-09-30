"""Pas 1. Llegeix V77.psb (només lectura) i desa, de cada capa de filtre i de la base:
el llenç sencer reduït ÷5 i la zona central de ±1500 px reduïda ÷2. També la base amb marge (±2300 px) i la imatge fusionada."""
import numpy as np, time
from comu import *
from psb69 import PSB
CAPES=[3,41,43,44,45,47,51,53,54,55,56]
p=PSB(str(PSB_V77)); print('V77',p.width,'x',p.height,len(p.layers),'capes')
for lid in CAPES:
    t=time.time(); L=p.layer(lid); rgb=np.stack([p.channel(lid,c)[0] for c in (0,1,2)],-1); ox,oy=L['left'],L['top']
    assert (ox,oy)==(0,0) and rgb.shape[:2]==(p.height,p.width), 'aquestes capes ocupen tot el llenç'
    np.save(TREBALL/'capes'/f'L{lid}_full5.npy',redueix(rgb.astype(np.float32),5).astype(np.float32))
    x0,y0=int(CX)-1500,int(CY)-1500
    np.save(TREBALL/'capes'/f'L{lid}_centre2.npy',redueix(rgb[y0:y0+3000,x0:x0+3000].astype(np.float32),2).astype(np.float32))
    if lid==3:
        x1,y1=int(CX)-2300,int(CY)-2300
        np.save(TREBALL/'capes'/'L3_gran2.npy',redueix(rgb[y1:y1+4600,x1:x1+4600].astype(np.float32),2).astype(np.float32))
    print(lid,L['name'],'%.0fs'%(time.time()-t),flush=True)
C=p.composite()[...,:3].astype(np.float32)
np.save(TREBALL/'capes'/'compost_full5.npy',redueix(C,5).astype(np.float32))
x0,y0=int(CX)-1500,int(CY)-1500
np.save(TREBALL/'capes'/'compost_centre2.npy',redueix(C[y0:y0+3000,x0:x0+3000],2).astype(np.float32))
print('fet')
