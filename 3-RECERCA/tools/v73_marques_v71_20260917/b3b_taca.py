import sys, json, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'
sys.path.insert(0,NEW)
import compo71; from compo71 import *
from scipy.ndimage import gaussian_filter
CX,CY,RS=998.88,998.41,456.0
m=np.load(NEW+'/marques_219.npz'); Mk=np.zeros((2000,2000),np.float32); mx,my=int(m['x0'])-4377,int(m['y0'])-2777; Mk[my:my+m['A'].shape[0],mx:mx+m['A'].shape[1]]=m['A']/65535
R7=np.zeros((2000,2000),bool); R7[3928-2777:4132-2777,5187-4377:5418-4377]=Mk[3928-2777:4132-2777,5187-4377:5418-4377]>0.03
Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); yb,xb=np.nonzero(R7); rb=np.hypot(xb-CX,yb-CY); anell=(rr>=rb.min()-10)&(rr<=rb.max()+10)&(~R7)&(rr<RS-8)
print('marca 219.7: %d px, r %.0f–%.0f'%(R7.sum(),rb.min(),rb.max()))
def taca(C,nom):
    Lc=C.mean(-1); Ls=gaussian_filter(Lc,8); print(f'  {nom:52s}: dins {Lc[R7].mean():.4f} anell {Lc[anell].mean():.4f} → {100*(1-Lc[R7].mean()/Lc[anell].mean()):+.1f} % sota l\'anell (mín suavitzat {100*(1-Ls[R7].min()/Lc[anell].mean()):+.1f} %)')
F=np.load(NEW+'/roi71_recomp.npz'); taca(F['C'].astype(np.float32)/65535,'compost de Pere (V71: WOW obert, POWAAAH3 visible)')
compo71.OVERRIDE.clear()
for excl,nom in (((219,220,56),'sense WOW bilateral 56'),((219,220,57),'sense POWAAAH3 57'),((219,220,56,57),'sense 56 ni 57')):
    C,_=recompon(exclou=excl); taca(C,nom)
rgb30,_=carrega(30); taca(rgb30,'capa lunar 30 sola (V71, vel restat)')
rgb57,a57=carrega(57); taca(rgb57,'POWAAAH3 57 sola (RGB)')
rgb56,a56=carrega(56); print('  WOW 56: valor mitjà del filtre dins de la marca %.3f, a l\'anell %.3f; màscara dins del disc mitjana %.3f'%(rgb56.mean(-1)[R7].mean(),rgb56.mean(-1)[anell].mean(),(a56/(51/255))[rr<440].mean()))
# perfils de color fins al limbe (pas 1 px) de la base sola: R/G i B/G per sector, r 452…500
from scipy.ndimage import map_coordinates
RR=np.arange(450,521,1.0)
def perfil(img,az0,az1):
    th=np.deg2rad(np.arange(az0,az1,0.25)); xs=CX+RR[None,:]*np.cos(th[:,None]); ys=CY-RR[None,:]*np.sin(th[:,None])
    return np.median(map_coordinates(img,[ys.ravel(),xs.ravel()],order=1,mode='nearest').reshape(len(th),len(RR)),0)
rgb3,a3=carrega(3); S=np.load(NEW+'/roi71_recomp_sensefiltres.npz'); Cs=S['C'].astype(np.float32)/65535
print('\nbase 3 sola i compost sense filtres: R/G i B/G, r 452…520 pas 4, sectors E/N/W/S')
for nom,(a0,a1) in (('E 0–60',(0,60)),('N 60–120',(60,120)),('W 150–210',(150,210)),('S 240–300',(240,300))):
    for tag,C in (('base',rgb3),('sense filtres',Cs)):
        rg=perfil(C[...,0]/np.maximum(C[...,1],1e-4),a0,a1); bg=perfil(C[...,2]/np.maximum(C[...,1],1e-4),a0,a1)
        print(f'{nom:9s} {tag:14s} R/G: '+' '.join(f'{x:5.3f}' for x in rg[2::4])+' | B/G: '+' '.join(f'{x:5.3f}' for x in bg[2::4]))
