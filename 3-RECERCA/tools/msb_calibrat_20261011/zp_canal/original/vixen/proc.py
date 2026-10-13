#!/usr/bin/env python3
"""Per a cada un dels 8 fotogrames de cerca: RAW − master, màscara sat|calents
dilatada 3×3, pla verd interpolat, fons+sigma, mapa S/N i DAOStarFinder
(threshold 4.0, fwhm 3.2, roundness ±1.5, sharpness 0.05–2.0) → catàleg brut.

Origen: rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/vixen/proc.py
Canvis: només el bloc comu + os.chdir(comu.work("vixen")); els CR3 surten de
lib.DIR (comu.DADES_VIXEN_UNF) i els masters/sortides del cwd de treball.
Nota: fa servir l'API antiga de photutils (roundlo/roundhi, sharplo/sharphi,
tb['xcentroid']); amb photutils 3.0.0 funciona amb AstropyDeprecationWarning
(comprovat el 17-08-2026); a 4.0 caldrà roundness_range=(-1.5,1.5),
sharpness_range=(0.05,2.0) i 'x_centroid'/'y_centroid', mateixos valors.
Sortida: ~4,5 GB de .npy (snr/res/sig/msk per fotograma) + cat_*.npy + ndet.json.
"""
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("vixen"))

import numpy as np, lib, time, json
from scipy import ndimage as ndi
from photutils.detection import DAOStarFinder

FRAMES=[('572A2978',1.0,'1'),('572A2979',2.0,'2'),('572A2980',2.0,'2'),('572A2981',2.0,'2'),
        ('572A2982',10.3,'10'),('572A2983',10.3,'10'),('572A2984',10.3,'10'),('572A2996',1.0,'1')]
hm={k:lib.hotmask('dark_med_%s.npy'%k) for k in ['1','2','10']}
dk={k:np.load('dark_med_%s.npy'%k)[:lib.H,:lib.W] for k in ['1','2','10']}
cat={}
for f,exp,dkey in FRAMES:
    t0=time.time()
    im=lib.load_raw(f)
    sat=im>=lib.SAT
    im=im-dk[dkey]
    bad=ndi.binary_dilation(sat|hm[dkey],np.ones((3,3)))
    g=lib.green_full(im,bad)
    mask=~np.isfinite(g)
    bg,sig,res=lib.bg_and_sigma(g,bs=24,mask=mask)
    snr=np.where(mask,0.0,res/sig).astype(np.float32)
    np.save('snr_%s.npy'%f,snr); np.save('res_%s.npy'%f,res); np.save('sig_%s.npy'%f,sig); np.save('msk_%s.npy'%f,mask)
    d=DAOStarFinder(threshold=4.0,fwhm=3.2,roundlo=-1.5,roundhi=1.5,sharplo=0.05,sharphi=2.0,exclude_border=True)
    tb=d(snr)
    n=0 if tb is None else len(tb)
    if tb is not None:
        arr=np.array([tb['xcentroid'],tb['ycentroid'],tb['peak'],tb['flux'],tb['roundness1'],tb['roundness2'],tb['sharpness']]).T
        np.save('cat_%s.npy'%f,arr)
    cat[f]=n
    print('%s exp=%.1f sat=%.4f sigma=%.1f bg=%.0f  det=%d  %.1fs'%(f,exp,sat.mean(),np.median(sig[~mask]),np.median(bg),n,time.time()-t0))
json.dump(cat,open('ndet.json','w'))
