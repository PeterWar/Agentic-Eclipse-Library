"""A22: les fotos (76/96/204) a la zona de ploma (15–40 px fora del limbe): són més fosques que el compost de sota? perfils amb/sense fotos (V70 filtres) i quocient foto/compost-sota per sector."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
import compo; from compo import *
from scipy.ndimage import map_coordinates
CX,CY,RS=998.88,998.41,456.0
for lid in (47,49,51,53,55,56,30,3,41,42,45,46): compo.OVERRIDE[lid]=SP+f'/roi_L{lid}_v70.npz'
Cs,as_=recompon(exclou=(218,76,96,204,206)); Ca,aa=recompon()
RR=np.arange(440,520,0.25)
def perfil(img,az0,az1):
    th=np.deg2rad(np.arange(az0,az1,0.25)); xs=CX+RR[None,:]*np.cos(th[:,None]); ys=CY-RR[None,:]*np.sin(th[:,None])
    return np.median(map_coordinates(img,[ys.ravel(),xs.ravel()],order=1,mode='nearest').reshape(len(th),len(RR)),0)
sectors={'m2 NW':(148,158),'m3-4 W':(163,173),'m5 Weq':(177,181),'m6 WSW':(189,199),'ctrl NNW':(110,125),'ctrl SW':(215,230)}
for kk,(a0,a1) in sectors.items():
    ps=perfil(Cs.mean(-1),a0,a1); pa=perfil(Ca.mean(-1),a0,a1); rgb76,a76=carrega(76); p76=perfil(rgb76.mean(-1),a0,a1); al76=perfil(a76,a0,a1); rgb96,a96=carrega(96); al96=perfil(a96,a0,a1)
    print(f'\n{kk}   r:      '+' '.join(f'{x:5.0f}' for x in RR[::12]))
    print('   sense fotos: '+' '.join(f'{x:5.3f}' for x in ps[::12])); print('   amb fotos  : '+' '.join(f'{x:5.3f}' for x in pa[::12])); print('   quocient   : '+' '.join(f'{x:5.3f}' for x in (pa/np.maximum(ps,1e-6))[::12]))
    print('   L76 RGB    : '+' '.join(f'{x:5.3f}' for x in p76[::12])); print('   L76 alfa   : '+' '.join(f'{x:5.3f}' for x in al76[::12])); print('   L96 alfa   : '+' '.join(f'{x:5.3f}' for x in al96[::12]))
# quocient foto76/compost-sota on 76 té alfa 0,1–0,7 i no és protuberància (R/G < 1,8), r > RS+6: mediana per sector de 10°
yy,xx=np.mgrid[0:2000,0:2000]; rr=np.hypot(xx-CX,yy-CY); az=np.rad2deg(np.arctan2(-(yy-CY),xx-CX))%360
rgb76,a76=carrega(76); L76=rgb76.mean(-1); Ls=Cs.mean(-1); rg=rgb76[...,0]/np.maximum(rgb76[...,1],1e-4)
k=(a76>0.1)&(a76<0.7)&(rr>RS+6)&(rr<RS+60)&(rg<1.8)&(as_>0.99)
print('\nquocient L76/compost-sota (ploma, no protuberància) per sector de 10°:')
for s in range(90,250,10):
    kk=k&(az>=s)&(az<s+10)
    if kk.sum()>200: print(f'  az {s:3d}–{s+10:3d}: n={int(kk.sum()):6d}  mediana {np.median(L76[kk]/Ls[kk]):.3f}   (R {np.median(rgb76[...,0][kk]/Cs[...,0][kk]):.3f} G {np.median(rgb76[...,1][kk]/Cs[...,1][kk]):.3f} B {np.median(rgb76[...,2][kk]/Cs[...,2][kk]):.3f})')
