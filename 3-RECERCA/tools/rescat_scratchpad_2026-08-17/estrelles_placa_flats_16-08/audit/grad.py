import sys, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
from esfcmp import *
from run import TRAINS
for train,n in [('vixen','572A2987'),('sony','DSC06981')]:
    t=TRAINS[train]
    v,c,white=load(t['dirp']+n+t['ext'])
    x,y,val=pick(v,c,'G')
    cx,cy,R=centroid(v)
    for w in (60.,25.): cx,cy,R,sd,ng=fit_circle(x,y,val,cx,cy,R,win=w)
    r=(np.hypot(x-cx,y-cy)-R)*t['scale']
    print(train,n,'R_as=%.1f'%(R*t['scale']))
    for lo in range(5,60,5):
        m=(r>lo)&(r<lo+5)
        print('   u=%3d-%3d as  mediana=%9.1f  n=%d'%(lo,lo+5,np.median(val[m]),m.sum()))
