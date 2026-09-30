"""B3: l'anell verdós de la part linealitzada: perfils radials per sector (lluminància i quocient verd G/((R+B)/2)) del compost sense filtres i de cada capa que hi contribueix (3, 57, 30, 76, 96, 204); i la taca (219.7) al compost de Pere."""
import sys, json, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'
sys.path.insert(0,NEW)
import compo71; from compo71 import *
from scipy.ndimage import map_coordinates, gaussian_filter
CX,CY,RS=998.88,998.41,456.0; RR=np.arange(430,620,1.0)
def perfil(img,az0,az1):
    th=np.deg2rad(np.arange(az0,az1,0.25)); xs=CX+RR[None,:]*np.cos(th[:,None]); ys=CY-RR[None,:]*np.sin(th[:,None])
    return np.median(map_coordinates(img,[ys.ravel(),xs.ravel()],order=1,mode='nearest').reshape(len(th),len(RR)),0)
S=np.load(NEW+'/roi71_recomp_sensefiltres.npz'); Cs=S['C'].astype(np.float32)/65535; as_=S['a'].astype(np.float32)/65535
verd=lambda C: C[...,1]/np.maximum((C[...,0]+C[...,2])/2,1e-4)
print('== compost SENSE filtres: quocient verd G/((R+B)/2) per sector, r 440…600 (pas 10) ==')
sectors=[(0,30),(30,60),(60,90),(90,120),(120,150),(150,180),(180,210),(210,240),(240,270),(270,300),(300,330),(330,360)]
print('sector      '+' '.join(f'{int(r):5d}' for r in RR[10::10]))
V=verd(Cs)
for a0,a1 in sectors:
    p=perfil(V,a0,a1); print(f'{a0:3d}–{a1:3d}    '+' '.join(f'{x:5.3f}' for x in p[10::10]))
# per capa: alfa efectiva i quocient verd, sectors E (0–60) i W (150–210) i S (240–300)
print('\n== per capa: alfa efectiva (mitjana sector) i quocient verd de la capa, r 440…560 (pas 10) ==')
for lid in (3,57,30,76,96,204,206):
    rgb,a=carrega(lid); Vl=verd(rgb)
    for nom,(a0,a1) in (('E 0–60',(0,60)),('N 60–120',(60,120)),('W 150–210',(150,210)),('S 240–300',(240,300))):
        pa=perfil(a,a0,a1); pv=perfil(Vl,a0,a1); pl=perfil(rgb.mean(-1),a0,a1)
        print(f'capa {lid:3d} {nom:10s} alfa: '+' '.join(f'{x:5.2f}' for x in pa[10:131:10])+' | verd: '+' '.join(f'{x:5.3f}' for x in pv[10:131:10])+' | L: '+' '.join(f'{x:5.3f}' for x in pl[10:131:10]))
# el compost sense filtres: lluminància per sector
print('\n== compost SENSE filtres: lluminància, r 440…600 ==')
L=Cs.mean(-1)
for a0,a1 in sectors[::3]:
    p=perfil(L,a0,a1); print(f'{a0:3d}–{a1:3d}    '+' '.join(f'{x:5.3f}' for x in p[10::10]))
# la taca 219.7 al compost de Pere (des-fusionat de les marques) i sense la capa 56 (WOW bilateral oberta) i sense 57
F=np.load(NEW+'/roi71_recomp.npz'); Cf=F['C'].astype(np.float32)/65535
m=np.load(NEW+'/marques_219.npz'); Mk=np.zeros((2000,2000),np.float32); mx,my=int(m['x0'])-4377,int(m['y0'])-2777; Mk[my:my+m['A'].shape[0],mx:mx+m['A'].shape[1]]=m['A']/65535
R7=np.zeros((2000,2000),bool); R7[3928-2777:4132-2777,5187-4377:5418-4377]=Mk[3928-2777:4132-2777,5187-4377:5418-4377]>0.2
Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); yb,xb=np.nonzero(R7); rb=np.hypot(xb-CX,yb-CY); anell=(rr>=rb.min()-10)&(rr<=rb.max()+10)&(~R7)&(rr<RS-8)
def taca(C,nom):
    Lc=C.mean(-1); print(f'taca 219.7 {nom}: dins {Lc[R7].mean():.4f} anell {Lc[anell].mean():.4f} → {100*(1-Lc[R7].mean()/Lc[anell].mean()):+.1f} % sota l\'anell')
taca(Cf,'compost de Pere (V71 amb WOW obert i POWAAAH3 visible)')
compo71.OVERRIDE.clear(); C56,_=recompon(exclou=(219,220,56)); taca(C56,'sense WOW bilateral (56)')
C57,_=recompon(exclou=(219,220,57)); taca(C57,'sense POWAAAH3 (57)')
rgb30,a30=carrega(30); taca(rgb30,'capa lunar 30 sola')
rgb56,a56=carrega(56); Y0=a56/(51/255); print('WOW bilateral 56: màscara mitjana dins del disc (r<440) %.3f; valor mitjà del filtre dins del disc %.3f'%(Y0[rr<440].mean(),rgb56.mean(-1)[rr<440].mean()))
rgb57,a57=carrega(57); print('POWAAAH3 57: alfa efectiva mitjana dins del disc %.3f, a r 456–480 %.3f, a r 480–600 %.3f, a r>800 %.3f'%(a57[rr<440].mean(),a57[(rr>456)&(rr<480)].mean(),a57[(rr>480)&(rr<600)].mean(),a57[rr>800].mean()))
