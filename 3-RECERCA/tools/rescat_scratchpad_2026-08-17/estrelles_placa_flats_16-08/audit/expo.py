"""La tendencia FWHM vs temps d'exposicio del Vixen, es real o es una seleccio
de sectors? Als 1/8 s la meitat dels sectors cauen per saturacio."""
import sys, numpy as np, math
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
from esfcmp import *
from run import TRAINS
t=TRAINS['vixen']
def fits_of(name):
    v,c,white=load(t['dirp']+name+t['ext'])
    x,y,val=pick(v,c,'G')
    cx,cy,R=centroid(v)
    for w in (60.,25.): cx,cy,R,sd,ng=fit_circle(x,y,val,cx,cy,R,win=w)
    return sector_fits(x,y,val,cx,cy,R,30./t['scale'],240,(white-512)*0.93)
def fw(fits,keep=None):
    f=[q for q in fits if keep is None or q['a'] in keep]
    if len(f)<20: return None,len(f)
    xc,ym,e,cnt=stack_esf(f,align=True,xlim=20./t['scale'],bw=0.05)
    return fit_esf(xc,ym,e,boxw=1.0)['fwhm_tot']*t['scale'],len(f)
groups=[('572A2985','1/2000'),('572A2986','1/500'),('572A2987','1/125'),('572A2988','1/30'),('572A2989','1/8')]
G2=[('572A2997','1/2000'),('572A2998','1/500'),('572A2999','1/125'),('572A3000','1/30'),('572A3001','1/8')]
G3=[('572A3003','1/2000'),('572A3004','1/500'),('572A3005','1/125'),('572A3006','1/30'),('572A3007','1/8')]
for G in (groups,G2,G3):
    F={n:fits_of(n) for n,_ in G}
    common=set.intersection(*[{q['a'] for q in F[n]} for n,_ in G])
    print(f"  --- recorregut {G[0][0]}..{G[-1][0]}   sectors comuns={len(common)}")
    for n,e in G:
        a,na=fw(F[n]); b,nb=fw(F[n],common)
        snr=np.median([q['snr'] for q in F[n]])
        print(f"    {n} {e:7s} tots({na:3d})={a:5.2f}\"   comuns({nb:3d})={b:5.2f}\"  S/N={snr:.0f}",flush=True)
