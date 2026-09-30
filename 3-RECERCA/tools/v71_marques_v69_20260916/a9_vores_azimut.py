"""A9: radi de cada vora (50 %) per sector de 10°, referit al centre de la silueta fotogràfica (perles 96): on l'alfa lunar sobresurt de la silueta i on el forat de la base no arriba."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.ndimage import map_coordinates
Rr=np.load(SP+'/roi_recomp.npz'); Cr=Rr['C'].astype(np.float32)/65535
v=json.load(open(SP+'/a5_vores.json')); s=v['perles 96 RGB (silueta)']
CX=5377-4377+s['dx']; CY=3777-2777-s['dy']   # centre de la silueta fotogràfica (dy reportat = −x2 → y imatge = CY0 − dy... comprovat amb el signe del fit)
# comprovació del signe: refem el fit de la silueta 96 amb aquest centre → dx,dy han de ser ≈0
TH=np.deg2rad(np.arange(0,360,0.25)); RR=np.arange(400,520,0.25)
def perfils(img,cx,cy):
    xs=cx+RR[None,:]*np.cos(TH[:,None]); ys=cy-RR[None,:]*np.sin(TH[:,None]); return map_coordinates(img,[ys.ravel(),xs.ravel()],order=1,mode='nearest').reshape(len(TH),len(RR))
def vora_50(P):
    lo=np.median(P[:,(RR>=400)&(RR<=430)],1); hi=np.median(P[:,(RR>=480)&(RR<=510)],1); mid=(lo+hi)/2; out=np.full(len(TH),np.nan)
    for i in range(len(TH)):
        p=P[i]; sg=np.sign(p-mid[i]); j=np.nonzero(np.diff(sg)!=0)[0]
        if len(j): k=j[0]; out[i]=RR[k]+(mid[i]-p[k])/(p[k+1]-p[k]+1e-12)*(RR[k+1]-RR[k])
    return out
def cercle(r):
    ok=np.isfinite(r); A=np.stack([np.ones(ok.sum()),np.cos(TH[ok]),np.sin(TH[ok])],1); b=r[ok]; x,*_=np.linalg.lstsq(A,b,rcond=None); return x
for cy_try in (3777-2777-s['dy'], 3777-2777+s['dy']):
    rgb,a=carrega(96); x=cercle(vora_50(perfils(rgb.mean(-1),CX,cy_try))); print('centre prova (%.2f,%.2f) → R %.2f dx %.2f x2 %.2f'%(CX,cy_try,x[0],x[1],x[2]))
    if abs(x[1])<0.3 and abs(x[2])<0.3: CY=cy_try
print('centre físic (silueta 96) ROI:',round(CX,2),round(CY,2),'→ absolut',round(CX+4377,2),round(CY+2777,2))
vores={}
for lid,nom,tipus in [(96,'silueta perles 96','L'),(204,'silueta perles 204','L'),(76,'silueta interiors 76','L'),(30,'alfa earthshine','a'),(3,'alfa base (forat)','a'),(76,'alfa interiors 76','a')]:
    rgb,a=carrega(lid); img=rgb.mean(-1) if tipus=='L' else a/(LAYERS[lid]['opacity']/255.0); vores[nom]=vora_50(perfils(img,CX,CY))
vores['compost (lluminància)']=vora_50(perfils(Cr.mean(-1),CX,CY))
np.savez_compressed(SP+'/a9_vores.npz',TH=TH,**{k.replace(' ','_'):v for k,v in vores.items()})
print('\nradi 50 % per sector de 10° (mediana), referit al centre físic:')
print('sector'.ljust(12)+''.join(f'{k[:16]:>18s}' for k in vores))
for a0 in range(0,360,10):
    k=(np.rad2deg(TH)>=a0)&(np.rad2deg(TH)<a0+10); row=f'{a0:3d}–{a0+10:3d}    '
    for nom,r in vores.items(): row+=f'{np.nanmedian(r[k]):18.1f}'
    print(row)
print('\nglobal: ', {k:(round(float(np.nanmedian(r)),2),round(float(np.nanstd(r)),2)) for k,r in vores.items()})
