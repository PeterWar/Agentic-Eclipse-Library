import sys, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/audit')
from sim import make, run
from esfcmp import sector_fits, stack_esf, fit_esf, fwhm_of
import numpy as np

def run2(scale,fwhm_as,c0,sigma_read,topo,xlim_as=20.,win_as=30.,flat=False,align=True):
    img,c,R,cen=make(scale,977.0,fwhm_as,c0,0.0,sigma_read,topo if topo>0 else 1e-9)
    if flat:  # sense corona: esglao pla a fora
        pass
    mm=(c==1)|(c==3); ys,xs=np.nonzero(mm); val=img[ys,xs]
    fits=sector_fits(xs.astype(float),ys.astype(float),val,cen-0.5,cen-0.5,R,win_as/scale,240,1e9)
    xc,ym,e,cnt=stack_esf(fits,align=align,xlim=xlim_as/scale,bw=0.05)
    f=fit_esf(xc,ym,e,boxw=1.0)
    s=fwhm_as/2.3548/scale
    return fwhm_of(1.,s,s,1.)*scale, f['fwhm_tot']*scale

print("VIXEN scale 2.158 -- efecte del soroll, de la topografia i del rang d'ajust")
for fw in (4.0,4.6,5.5,6.5):
    row=[]
    for lab,kw in [('nominal',dict(sigma_read=3.,topo=3.0,xlim_as=20.)),
                   ('sense soroll',dict(sigma_read=1e-6,topo=3.0,xlim_as=20.)),
                   ('sense topo',dict(sigma_read=3.,topo=0.0,xlim_as=20.)),
                   ('net+xlim30',dict(sigma_read=1e-6,topo=0.0,xlim_as=30.)),
                   ('xlim=30',dict(sigma_read=3.,topo=3.0,xlim_as=30.)),
                   ('sense alinear',dict(sigma_read=3.,topo=0.0,xlim_as=20.,align=False))]:
        esp,mes=run2(2.158,fw,830.,**kw); row.append((lab,esp,mes))
    print(f" in={fw:4.2f} esperat={row[0][1]:5.2f} | "+" | ".join(f"{l}={m:5.2f}" for l,e,m in row))
print()
print("SONY scale 3.234")
for fw in (5.5,7.0,8.3,9.5):
    row=[]
    for lab,kw in [('nominal',dict(sigma_read=8.,topo=3.0,xlim_as=20.)),
                   ('sense soroll',dict(sigma_read=1e-6,topo=3.0,xlim_as=20.)),
                   ('sense topo',dict(sigma_read=8.,topo=0.0,xlim_as=20.)),
                   ('net+xlim30',dict(sigma_read=1e-6,topo=0.0,xlim_as=30.)),
                   ('xlim=30',dict(sigma_read=8.,topo=3.0,xlim_as=30.)),
                   ('sense alinear',dict(sigma_read=8.,topo=0.0,xlim_as=20.,align=False))]:
        esp,mes=run2(3.234,fw,2600.,**kw); row.append((lab,esp,mes))
    print(f" in={fw:4.2f} esperat={row[0][1]:5.2f} | "+" | ".join(f"{l}={m:5.2f}" for l,e,m in row))
