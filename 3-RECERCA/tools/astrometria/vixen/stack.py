#!/usr/bin/env python3
"""Pila completa dels 8 fotogrames: shift bilineal de res/ok/sig amb −(dx,dy), pes (exp/sig)², flux en ADU/s de píxel verd → stack_flux/sig/snr.npy.

Origen: rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/vixen/stack.py
Canvis: només el bloc comu + os.chdir(comu.work("vixen")); cap constant,
llindar ni ordre de fotogrames tocat.
"""
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("vixen"))

import numpy as np, json, time
from scipy import ndimage as ndi
FR=[('572A2978',1.0,73742.55),('572A2979',2.0,73744.45),('572A2980',2.0,73747.35),('572A2981',2.0,73750.26),
    ('572A2982',10.3,73753.41),('572A2983',10.3,73766.48),('572A2984',10.3,73779.88),('572A2996',1.0,73804.26)]
SH=json.load(open('shifts_start.json'))
H,W=4638,6958
num=np.zeros((H,W),np.float32); den=np.zeros((H,W),np.float32)
for f,exp,t in FR:
    dt,dx,dy=SH[f]
    res=np.load('res_%s.npy'%f); sig=np.load('sig_%s.npy'%f); msk=np.load('msk_%s.npy'%f)
    res=np.where(msk,0.0,res).astype(np.float32)
    ok=(~msk).astype(np.float32)
    rs=ndi.shift(res,(-dy,-dx),order=1,mode='constant',cval=0.0,prefilter=False)
    os_=ndi.shift(ok,(-dy,-dx),order=1,mode='constant',cval=0.0,prefilter=False)
    ss=ndi.shift(sig,(-dy,-dx),order=1,mode='nearest',prefilter=False)
    good=os_>0.99
    w=np.where(good,(exp/np.maximum(ss,1e-3))**2,0.0).astype(np.float32)
    num+=w*np.where(good,rs/exp,0.0); den+=w
    print(f,'done')
    del res,sig,msk,rs,os_,ss,w,good
flux=np.where(den>0,num/np.maximum(den,1e-12),0.0).astype(np.float32)     # ADU/s
sflx=np.where(den>0,1.0/np.sqrt(np.maximum(den,1e-12)),np.inf).astype(np.float32)
snr=np.where(den>0,flux/sflx,0.0).astype(np.float32)
np.save('stack_flux.npy',flux); np.save('stack_sig.npy',sflx); np.save('stack_snr.npy',snr)
v=snr[den>0]
print('stack snr percentiles',np.percentile(v,[1,50,99,99.9,99.99]),v.max())
for T in [4,5,6,8]:
    print(' >%d: %d px'%(T,(snr>T).sum()))
print('median flux sigma (ADU/s) %.3f'%np.median(sflx[den>0]))
