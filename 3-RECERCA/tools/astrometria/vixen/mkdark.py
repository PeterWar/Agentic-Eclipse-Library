#!/usr/bin/env python3
"""Masters de fosc del R6 III per a la cadena d'estrelles: mediana per píxel de
tots els darks amb ExposureTime EXIF exactament '10' (els de 10,3 s), '2' i '1'.

Origen: rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/vixen/mkdark.py
Canvis: D surt de comu.DARKS_R6; exiftool es busca amb shutil.which; les
sortides dark_med_{10,2,1}.npy van a comu.work("vixen"). Cap altre canvi:
mediana (no mitjana), sense retall (4639×6959), mateix ordre de fitxers (sorted).
"""
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("vixen"))

import rawpy, numpy as np, glob, subprocess, shutil
D=str(comu.DARKS_R6)+'/'
EXIFTOOL=shutil.which('exiftool')
if not EXIFTOOL:
    sys.exit("mkdark.py: no trobo 'exiftool' al PATH (brew install exiftool)")
out=subprocess.run([EXIFTOOL,'-q','-n','-T','-FileName','-ExposureTime','-CameraTemperature']+sorted(glob.glob(D+'*.CR3')),capture_output=True,text=True).stdout
rows=[l.split('\t') for l in out.strip().split('\n')]
for exp in ['10','2','1']:
    fs=[r[0] for r in rows if r[1]==exp]
    print(exp,'n=',len(fs))
    stack=[]
    for f in fs:
        r=rawpy.imread(D+f); stack.append(r.raw_image_visible.astype(np.float32)); r.close()
    st=np.stack(stack); del stack
    med=np.median(st,axis=0)
    np.save(f'dark_med_{exp}.npy',med.astype(np.float32))
    print('  median-of-medians pedestal', np.median(med), 'p1',np.percentile(med,1),'p99',np.percentile(med,99),'max',med.max())
    del st, med
