import sys, numpy as np, math
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
from esfcmp import *
from run import TRAINS
V="/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/"
S="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
for train,names in [('vixen',['572A2985','572A2987','572A2989','572A2999','572A3007']),
                    ('sony',['DSC06973','DSC06979','DSC06981','DSC06995','DSC07003'])]:
    t=TRAINS[train]
    for n in names:
        v,c,white=load(t['dirp']+n+t['ext'])
        raw=v+512
        x,y,val=pick(v,c,'G')
        cx,cy,R=centroid(v)
        for w in (60.,25.): cx,cy,R,sd,ng=fit_circle(x,y,val,cx,cy,R,win=w)
        r=np.hypot(x-cx,y-cy)
        m=np.abs(r-R)<30.0/t['scale']
        vv=val[m]
        sat=(white-512)*0.93
        # nivell dins vs fora
        inn=np.median(val[(r<R-10/t['scale'])&(r>R-30/t['scale'])])
        out=np.median(val[(r>R+10/t['scale'])&(r<R+30/t['scale'])])
        print(f"{train:5s} {n} white={white} sat_thr={sat:.0f} maxADU_finestra={vv.max():.0f} "
              f"frac>sat={np.mean(vv>sat)*100:.4f}% frac>0.9white={np.mean(vv>(white-512)*0.9)*100:.4f}% "
              f"dins={inn:.0f} fora={out:.0f} maxADU_global={val.max():.0f}", flush=True)
