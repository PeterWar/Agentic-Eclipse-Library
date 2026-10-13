#!/usr/bin/env python3
"""Centre i radi del disc lunar (forat fosc dins la corona) a 16 fotogrames
curts del Vixen, al pla G1 menys pedestal 511,5, amb temps EXIF; ajust lineal
del moviment de la Lluna al sensor → center_fit.json.

Origen: rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/vixen/center2.py
Canvis: DIR surt de comu.DADES_VIXEN_UNF; exiftool amb shutil.which;
center_fit.json va a comu.work("vixen"). Cap altre canvi.
"""
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("vixen"))

import rawpy, numpy as np, subprocess, json, shutil
from scipy import ndimage as ndi
DIR=str(comu.DADES_VIXEN_UNF)+'/'
EXIFTOOL=shutil.which('exiftool')
if not EXIFTOOL:
    sys.exit("center2.py: no trobo 'exiftool' al PATH (brew install exiftool)")
fs=['572A2969','572A2970','572A2971','572A2972','572A2987','572A2988','572A2989','572A2990',
    '572A2999','572A3000','572A3001','572A3002','572A3005','572A3006','572A3007','572A3008']
out=subprocess.run([EXIFTOOL,'-q','-n','-T','-FileName','-DateTimeOriginal','-SubSecTimeOriginal','-ExposureTime']+[DIR+f+'.CR3' for f in fs],capture_output=True,text=True).stdout
t={}
for l in out.strip().split('\n'):
    a=l.split('\t'); hh,mm,ss=a[1].split(' ')[1].split(':')
    t[a[0][:8]]=int(hh)*3600+int(mm)*60+int(ss)+float('0.'+a[2].zfill(2))
res=[]
for f in fs:
    r=rawpy.imread(DIR+f+'.CR3'); im=r.raw_image_visible[:4638,:6958].astype(np.float64); r.close()
    a=im[0::2,1::2]-511.5
    lo=np.percentile(a,20); hi=np.percentile(a,99.9); T=lo+0.06*(hi-lo)
    B=ndi.binary_closing(a>T,np.ones((5,5)))
    holes=ndi.binary_fill_holes(B)&~B
    lab,n=ndi.label(holes); sizes=ndi.sum(holes,lab,range(1,n+1)); m=lab==int(np.argmax(sizes))+1
    ys,xs=np.nonzero(m); area=m.sum()
    res.append((f,t[f],2*xs.mean()+1,2*ys.mean(),2*np.sqrt(area/np.pi)))
    print('%s t=%.2f cx=%.2f cy=%.2f r=%.2f'%res[-1])
T0=res[0][1]
tt=np.array([r[1] for r in res])-T0
cx=np.array([r[2] for r in res]); cy=np.array([r[3] for r in res])
px=np.polyfit(tt,cx,1); py=np.polyfit(tt,cy,1)
print('linear fit vx=%.4f px/s vy=%.4f px/s  |v|=%.4f px/s = %.3f arcsec/s'%(px[0],py[0],np.hypot(px[0],py[0]),np.hypot(px[0],py[0])*2.158))
print('resid x rms %.2f  y rms %.2f'%(np.std(cx-np.polyval(px,tt)),np.std(cy-np.polyval(py,tt))))
print('mean radius %.2f px = %.1f arcsec'%(np.mean([r[4] for r in res]), np.mean([r[4] for r in res])*2.158))
json.dump({'T0':T0,'px':px.tolist(),'py':py.tolist(),'times':{r[0]:r[1] for r in res}},open('center_fit.json','w'))
