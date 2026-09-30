"""VORA v2: des del limbe (452 px), objectiu = mediana per anell lunar-cèntrica del BENCHMARK.
Parteix del perfil F100 i hi suma la diferència final (benchmark − D2 actual), amb sostre i suavitzat.
Sortida: vora_v2.npz i v5fix3.npy (interior + VORA v2)."""
import os, numpy as np, tifffile
from scipy.ndimage import gaussian_filter1d
D = os.path.dirname(os.path.abspath(__file__))
W,H = 7648,5353; LLUNA = (4034.8,2736.3)
yy,xx = np.mgrid[0:H,0:W].astype(np.float32)
r_ll = np.hypot(xx-LLUNA[0],yy-LLUNA[1])
def sstep(t):
    t=np.clip(t,0,1); return t*t*t*(t*(t*6-15)+10)
bm = tifffile.imread(os.path.expanduser('~/Downloads/Benchmark20Agost.tif')).astype(np.float32)/65535.0
d2 = np.load(os.path.join(D,'compost_D_pont_135_195_trim.npy')).astype(np.float32)/65535.0
rb = np.arange(446, 700, 2.0); rcx = 0.5*(rb[:-1]+rb[1:])
idx = np.digitize(r_ll.ravel(), rb)-1
Lm = np.zeros((len(rb)-1,3),np.float32); Dm = np.zeros((len(rb)-1,3),np.float32)
fb = bm.reshape(-1,3); fd = d2.reshape(-1,3)
for k in range(len(rb)-1):
    s = idx==k
    if s.sum()>500:
        Lm[k]=np.median(fb[s],axis=0); Dm[k]=np.median(fd[s],axis=0)
L = np.clip(Lm-Dm, 0, 0.09)
L = gaussian_filter1d(L, 2.5, axis=0, mode='nearest')
w2 = sstep((rcx-452.0)/16.0)
L = L*w2[:,None]
old = np.load(os.path.join(D,'vora_F100.npz'))
prof_old = np.zeros_like(L)
for c in range(3):
    prof_old[:,c] = np.interp(rcx, old['rcx'], old['prof'][:,c], left=0, right=0)
prof = np.clip(prof_old + L, 0, 0.12)
prof = gaussian_filter1d(prof, 1.5, axis=0, mode='nearest')
np.savez(os.path.join(D,'vora_v2.npz'), rcx=rcx, prof=prof)
print('perfil VORA v2 (lum×1000):')
for k in range(0, len(rcx), 8):
    print(f'  r_ll {rcx[k]:5.0f}: vell {prof_old[k].mean()*1000:5.1f}  +dif {L[k].mean()*1000:5.1f}  → nou {prof[k].mean()*1000:5.1f}')
c1 = np.load(os.path.join(D,'v5fix_compost.npy')).astype(np.float32)/65535.0
lift = np.zeros((H,W,3),np.float32)
for c in range(3):
    lift[...,c] = np.interp(r_ll, rcx, prof[:,c], left=0, right=0)
out = np.clip(c1+lift, 0, 1)
np.save(os.path.join(D,'v5fix3.npy'), np.clip(np.rint(out*65535),0,65535).astype(np.uint16))
print('v5fix3 desat')
