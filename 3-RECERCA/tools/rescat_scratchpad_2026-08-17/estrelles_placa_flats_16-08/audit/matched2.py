import sys, numpy as np, math
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/audit')
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
from matched import solar as solar_nom, hough, sfs, DIR, EXT
from esfcmp import load,pick,fit_circle,stack_esf,fit_esf
from run import TRAINS
def solar(train,name,useR='fit'):
    t=TRAINS[train]
    v,c,white=load(DIR[train]+name+EXT[train])
    x,y,val=pick(v,c,'G')
    Rpx=946.0/t['scale']
    cx,cy=hough(v,Rpx); R=Rpx
    for w in (40.,20.):
        cx,cy,R,sd,ng=fit_circle(x,y,-val,cx,cy,R,win=w)
        if abs(R*t['scale']-946)>60: R=Rpx
    Ruse=R if useR=='fit' else Rpx
    f=sfs(x,y,val,cx,cy,Ruse,30/t['scale'],240,(white-512)*0.93)
    if len(f)<15: return None
    xc,ym,e,cnt=stack_esf(f,align=True,xlim=20/t['scale'],bw=0.05)
    fit=fit_esf(xc,ym,e,boxw=1.0)
    return R*t['scale'],len(f),fit['fwhm_tot']*t['scale'],float(np.median([q['snr'] for q in f]))
print("SONY, sèrie temporal amb filtre (per veure QUAN es degrada)")
for n,tt in [('DSC06928','19:38:13'),('DSC06931','19:43:30'),('DSC06935','19:46:49'),
             ('DSC06944','19:50:39'),('DSC06946','20:01:22'),('DSC06951','20:12:04'),
             ('DSC06954','20:15:36'),('DSC06955','20:19:12'),('DSC06957','20:22:21'),
             ('DSC06960','20:23:50')]:
    r=solar('sony',n)
    print(f"  sony {n} {tt}  "+("REFUSAT" if not r else f"R={r[0]:.0f}\" sec={r[1]:3d} FWHM={r[2]:5.2f}\" S/N={r[3]:.0f}"),flush=True)
print()
print("VIXEN, mateixa cosa")
for n,tt in [('572A2907','19:01:14'),('572A2908','19:27:15'),('572A2909','19:51:17'),
             ('572A2914','20:01:10'),('572A2918','20:11:58'),('572A2921','20:15:11'),
             ('572A2922','20:19:07'),('572A2923','20:22:21'),('572A2926','20:23:50')]:
    r=solar('vixen',n)
    print(f"  vixen {n} {tt}  "+("REFUSAT" if not r else f"R={r[0]:.0f}\" sec={r[1]:3d} FWHM={r[2]:5.2f}\" S/N={r[3]:.0f}"),flush=True)
