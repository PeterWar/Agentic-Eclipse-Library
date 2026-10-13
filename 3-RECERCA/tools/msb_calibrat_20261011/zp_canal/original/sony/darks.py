#!/usr/bin/env python3
# Promogut de research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sony_stars/darks.py
# (sessio del 16-08-2026). Nomes canvien les rutes: dades i intermedis surten de comu.py.
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("sony"))
import rawpy, numpy as np, subprocess, os
DD=str(comu.DARKS_SONY)+"/"
out=subprocess.run(["exiftool","-T","-FileName","-ExposureTime",DD],capture_output=True,text=True).stdout
byexp={}
for ln in out.strip().split("\n"):
    p=ln.split("\t")
    if len(p)<2: continue
    byexp.setdefault(p[1].strip(),[]).append(p[0].strip())
for e in ["8","2","1"]:
    fl=sorted(byexp.get(e,[]))
    print(e,"s:",len(fl),"darks")
    fl=fl[:24]
    st=None
    for i,f in enumerate(fl):
        with rawpy.imread(DD+f) as r:
            v=r.raw_image_visible
        if st is None: st=np.empty((len(fl),)+v.shape,dtype=np.uint16)
        st[i]=v
    med=np.median(st,axis=0).astype(np.float32)
    np.save(f"masterdark_{e}s.npy", med)
    d=med-512.0
    print(f"   dark median={np.median(d):.2f} ADU, p99.9={np.percentile(d,99.9):.1f}, max={d.max():.0f}, n>50ADU={(d>50).sum()}")
    del st
