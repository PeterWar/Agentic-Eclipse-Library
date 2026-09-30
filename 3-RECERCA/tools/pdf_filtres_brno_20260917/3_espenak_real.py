"""Pas 3. La recepta d'Espenak (2000) aplicada a la nostra base (capa 00 de la V77):
c (original) → r (Radial Blur / Spin, 10°) → s = c − r (+ gris mitjà) → m = c × s. Centre a la Lluna, com a l'article. Coma flotant."""
import numpy as np, cv2, json
from comu import *
def gir(img,cx,cy,graus):
    """Desenfocament de gir: mitjana al llarg d'un arc de `graus` centrat a (cx,cy)."""
    H,W=img.shape[:2]; Nt=7200; Nr=int(np.ceil(np.hypot(max(cx,W-cx),max(cy,H-cy))))+2
    pol=cv2.warpPolar(img,(Nr,Nt),(cx,cy),Nr,cv2.WARP_POLAR_LINEAR|cv2.INTER_LINEAR)
    k=int(round(Nt*graus/360.0)); k+=1-(k%2)
    ext=np.concatenate([pol[-k:],pol,pol[:k]],0).astype(np.float64)
    cs=np.cumsum(np.concatenate([np.zeros((1,)+ext.shape[1:]),ext],0),0); caixa=((cs[k:]-cs[:-k])/k)[k-(k//2):k-(k//2)+Nt].astype(np.float32)
    return cv2.warpPolar(caixa,(W,H),(cx,cy),Nr,cv2.WARP_POLAR_LINEAR|cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
# zona central: es calcula amb marge (±2300 px) i s'ensenya ±1500 px, tot a ÷2
g=np.load(TREBALL/'capes'/'L3_gran2.npy')/65535.0
gx=(CX-(int(CX)-2300))/2-0.25; gy=(CY-(int(CY)-2300))/2-0.25; o=(2300-1500)//2
talla=lambda a: a[o:o+1500,o:o+1500]
r=gir(g,gx,gy,10.0); s=g-r; m=g*np.clip(0.5+s,0,1)
yy,xx=np.mgrid[0:1500,0:1500]; R=np.hypot(xx-(gx-o),yy-(gy-o)); lluna=R<(RLLUNA/2+1)
sl=talla(s).mean(-1); lim=float(np.percentile(np.abs(sl[(~lluna)&(R<3*RLLUNA/2)]),99.5))
jpg('pas_c',talla(g),w=900); jpg('pas_r',talla(r),w=900)
sv=np.clip(0.5+0.5*talla(s)/lim,0,1); sv[lluna]=0.5
jpg('pas_s',sv,w=900); jpg('pas_m',np.clip(talla(m)*2.0,0,1),w=900)     # «s» amb el contrast exagerat; «m» aclarida ×2
x0,y0,x1,y1=230,560,730,1060                                              # detall de la figura 5 (coordenades de la vista central ÷2)
jpg('det_espenak',sv[y0:y1,x0:x1],q=90,w=900)
for lid,nom in ((53,'det_achf'),(56,'det_wow')):
    jpg(nom,(np.load(TREBALL/'capes'/f'L{lid}_centre2.npy')/65535.0)[y0:y1,x0:x1],q=90,w=900)
# llenç sencer ÷5 de la «s»
c5=np.load(TREBALL/'capes'/'L3_full5.npy')/65535.0; cx,cy=CX/5-0.4,CY/5-0.4
s5=(c5-gir(c5,cx,cy,10.0)).mean(-1); dada=c5.mean(-1)>0.004
yy,xx=np.mgrid[0:s5.shape[0],0:s5.shape[1]]; R5=np.hypot(xx-cx,yy-cy)/(RLLUNA/5)
l5=float(np.percentile(np.abs(s5[(R5>1.05)&(R5<4)]),99.5)); v5=np.clip(0.5+0.5*s5/l5,0,1); v5[~dada]=0.5
jpg('esp_s',v5,w=1100)
json.dump(dict(angle_gir_graus=10.0,centre_llenc_px=[CX,CY],estirament_s_centre=lim,estirament_s_llenc=l5,caixa_detall_vista_central=[x0,y0,x1,y1]),open(REBUTS/'espenak_params.json','w'),indent=1)
print('fet')
