"""B6: l'anell verdós: quocients B/G i R/G de la base (3) en funció de la distància d al forat, per sectors de 10°, relatius al nivell a d 40–70; i el mateix al compost sense filtres. També el WOW 56 (ràster) a la vora del forat amb la màscara oberta."""
import sys, json, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
sys.path.insert(0,NEW)
import compo71; from compo71 import *
from scipy.ndimage import map_coordinates, gaussian_filter1d
CX,CY,RS=998.88,998.41,456.0
v=np.load(OLD+'/a9_vores.npz'); TH=v['TH']; r=v['alfa_base_(forat)'].copy(); ok=np.isfinite(r); r[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],r[ok]); R_hole=gaussian_filter1d(r,8,mode='wrap')
D=np.arange(-2,80,1.0)
def polar(img):
    xs=CX+(R_hole[:,None]+D[None,:])*np.cos(TH[:,None]); ys=CY-(R_hole[:,None]+D[None,:])*np.sin(TH[:,None]); return map_coordinates(img,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(D))
rgb3,a3=carrega(3); S=np.load(NEW+'/roi71_recomp_sensefiltres.npz'); Cs=S['C'].astype(np.float32)/65535
for nom,C in (('BASE 3',rgb3),('SENSE FILTRES',Cs)):
    bg=polar(C[...,2]/np.maximum(C[...,1],1e-4)); rg=polar(C[...,0]/np.maximum(C[...,1],1e-4)); A=polar(a3) if nom=='BASE 3' else np.ones_like(bg)
    bg[A<0.5]=np.nan; rg[A<0.5]=np.nan
    ref_b=np.nanmedian(bg[:,(D>=40)&(D<=70)],1); ref_r=np.nanmedian(rg[:,(D>=40)&(D<=70)],1)
    print(f'\n== {nom}: excés de B/G (%) respecte de d 40–70, per sector de 30° i d ==')
    print('sector    d: '+' '.join(f'{int(d):4d}' for d in D[2:42:3]))
    for s in range(0,360,30):
        k=(np.rad2deg(TH)>=s)&(np.rad2deg(TH)<s+30); e=100*(np.nanmedian(bg[k],0)/np.nanmedian(ref_b[k])-1); print(f'{s:3d}–{s+30:3d}      '+' '.join(f'{x:4.1f}' for x in e[2:42:3]))
    print(f'-- {nom}: excés de R/G (%) --')
    for s in range(0,360,90):
        k=(np.rad2deg(TH)>=s)&(np.rad2deg(TH)<s+90); e=100*(np.nanmedian(rg[k],0)/np.nanmedian(ref_r[k])-1); print(f'{s:3d}–{s+90:3d}      '+' '.join(f'{x:4.1f}' for x in e[2:42:3]))
# WOW 56 ràster i màscara de Pere a la vora
rgb56,a56=carrega(56); W=polar(rgb56.mean(-1)); Mk=polar(a56/(51/255))
print('\n== WOW bilateral 56 (V71 de Pere): valor del ràster i màscara per d, sectors de 90° ==')
for s in range(0,360,90):
    k=(np.rad2deg(TH)>=s)&(np.rad2deg(TH)<s+90); print(f'{s:3d}–{s+90:3d} valor: '+' '.join(f'{x:4.2f}' for x in np.nanmedian(W[k],0)[0:42:3])+' | màsc: '+' '.join(f'{x:4.2f}' for x in np.nanmedian(Mk[k],0)[0:42:3]))
print('valor mitjà del WOW dins del disc (d<-10):',float(rgb56.mean(-1)[np.hypot(*np.mgrid[0:2000,0:2000][::-1]-np.array([[[CX]],[[CY]]]))<440].mean()))
