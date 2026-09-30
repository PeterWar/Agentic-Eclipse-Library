"""Test d'acceptació d'Opus: mediana per anell lunar-cèntrica del candidat dins ±5% del benchmark
per r_ll 452-720 px, i sense cap mínim local (fossat) entre 452 i el pic."""
import os, sys, numpy as np, tifffile
D = os.path.dirname(os.path.abspath(__file__))
W,H=7648,5353; LLUNA=(4034.8,2736.3)
yy,xx=np.mgrid[0:H,0:W].astype(np.float32); r_ll=np.hypot(xx-LLUNA[0],yy-LLUNA[1])
cand=np.load(os.path.join(D,sys.argv[1])).astype(np.float32)/65535.0
bm=tifffile.imread(os.path.expanduser('~/Downloads/Benchmark20Agost.tif')).astype(np.float32)/65535.0
rb=np.arange(450,724,4.0); rcx=0.5*(rb[:-1]+rb[1:])
idx=np.digitize(r_ll.ravel(),rb)-1
lc=cand.mean(axis=2).ravel(); lb=bm.mean(axis=2).ravel()
ok=True; mins=[]
prev=None; puja_feta=False
print(' r_ll   cand    bench   raó')
vals=[]
for k in range(len(rb)-1):
    s=idx==k
    if s.sum()<500: continue
    mc=np.median(lc[s]); mb=np.median(lb[s]); rao=mc/max(mb,1e-6)
    vals.append((rcx[k],mc,mb,rao))
    if k%4==0: print(f'{rcx[k]:6.0f}  {mc*1000:6.1f}  {mb*1000:6.1f}  {rao:5.3f}')
    if not (0.95<=rao<=1.05): ok=False
# mínims locals del perfil del candidat (suavitzat lleu)
from scipy.ndimage import gaussian_filter1d
mcs=gaussian_filter1d(np.array([v[1] for v in vals]),1.5)
te_minim=False
pic=np.argmax(mcs)
for k in range(1,pic):
    if mcs[k] < mcs[k-1]-0.0015: te_minim=True
print('dins ±5% del benchmark a tot el rang?', ok)
print('cap mínim local abans del pic?', not te_minim)
