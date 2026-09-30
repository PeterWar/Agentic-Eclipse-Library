#!/usr/bin/env python3
"""Piles per grup: 'long' (3×10,3 s, shift cúbic) i 'short' (2×1 s + 3×2 s) → g_long_*/g_short_* (traça i FWHM per a fitpsf/fit2/cat_final).

Origen: rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/vixen/stack3.py
Canvis: només el bloc comu + os.chdir(comu.work("vixen")); cap constant,
llindar ni ordre de fotogrames tocat.
"""
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("vixen"))

import numpy as np, json
from scipy import ndimage as ndi
SH=json.load(open('shifts_start.json'))
H,W=4638,6958
groups={'long':[('572A2982',10.3),('572A2983',10.3),('572A2984',10.3)],
        'short':[('572A2978',1.0),('572A2979',2.0),('572A2980',2.0),('572A2981',2.0),('572A2996',1.0)]}
for gn,lst in groups.items():
    num=np.zeros((H,W),np.float32); den=np.zeros((H,W),np.float32)
    for f,exp in lst:
        dt,dx,dy=SH[f]
        res=np.load('res_%s.npy'%f); sig=np.load('sig_%s.npy'%f); msk=np.load('msk_%s.npy'%f)
        res=np.where(msk,0.0,res).astype(np.float32); ok=(~msk).astype(np.float32)
        rs=ndi.shift(res,(-dy,-dx),order=3,mode='constant',cval=0.0)
        os_=ndi.shift(ok,(-dy,-dx),order=1,mode='constant',cval=0.0,prefilter=False)
        ss=ndi.shift(sig,(-dy,-dx),order=1,mode='nearest',prefilter=False)
        good=os_>0.99
        w=np.where(good,(exp/np.maximum(ss,1e-3))**2,0.0).astype(np.float32)
        num+=w*np.where(good,rs/exp,0.0); den+=w
        del res,sig,msk,rs,os_,ss,w,good
    flux=np.where(den>0,num/np.maximum(den,1e-12),0.0).astype(np.float32)
    snr=np.where(den>0,flux*np.sqrt(np.maximum(den,1e-12)),0.0).astype(np.float32)
    np.save('g_%s_flux.npy'%gn,flux); np.save('g_%s_snr.npy'%gn,snr); np.save('g_%s_den.npy'%gn,den)
    print(gn,'max snr',snr.max())
