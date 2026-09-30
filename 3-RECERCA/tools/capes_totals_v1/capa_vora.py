"""Capa VORA: aixeca el fossat del limbe amb una corba radial centrada a la LLUNA (mediana per anell
del vel retirat), sense tornar les bombolles (comença a 455 px) i sense tocar la vora lunar estricta.
Variants F=0,5 i F=1,0. Sortides: vora_F*.npz (perfil), v5fix2_F*.npy (compost interior amb la capa)."""
import os, numpy as np
from scipy.ndimage import gaussian_filter1d
D = os.path.dirname(os.path.abspath(__file__))
W,H = 7648,5353; LLUNA = (4034.8,2736.3)
yy,xx = np.mgrid[0:H,0:W].astype(np.float32)
r_ll = np.hypot(xx-LLUNA[0],yy-LLUNA[1])
def sstep(t):
    t=np.clip(t,0,1); return t*t*t*(t*(t*6-15)+10)
c0 = np.load('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/47c293ed-2e8a-4c78-a543-00c84f771077/scratchpad/v5out/compost_rgb16.npy').astype(np.float32)/65535.0
c1 = np.load(os.path.join(D,'v5fix_compost.npy')).astype(np.float32)/65535.0
rb = np.arange(430, 640, 2.0); rcx = 0.5*(rb[:-1]+rb[1:])
idx = np.digitize(r_ll.ravel(), rb)-1
V = np.zeros((len(rb)-1,3), np.float32)
f0 = c0.reshape(-1,3); f1 = c1.reshape(-1,3)
for k in range(len(rb)-1):
    s = idx==k
    if s.sum()>500:
        V[k] = np.median(f0[s],axis=0) - np.median(f1[s],axis=0)
V = np.clip(V, 0, None)
V = gaussian_filter1d(V, 3.0, axis=0, mode='nearest')
w = sstep((rcx-455.0)/35.0)
print('perfil del vel (lum×1000) i pes:')
for k in range(0, len(rcx), 10):
    print(f'  r_ll {rcx[k]:5.0f}: V={V[k].mean()*1000:5.1f}  w={w[k]:.2f}')
for F in (0.5, 1.0):
    lift = np.zeros((H,W,3), np.float32)
    prof = V * w[:,None] * F
    for c in range(3):
        lift[...,c] = np.interp(r_ll, rcx, prof[:,c], left=0, right=0)
    out = np.clip(c1 + lift, 0, 1)
    np.save(os.path.join(D, f'v5fix2_F{int(F*100)}.npy'), np.clip(np.rint(out*65535),0,65535).astype(np.uint16))
    np.savez(os.path.join(D, f'vora_F{int(F*100)}.npz'), rcx=rcx, prof=prof)
    # perfil resultant, monotonia
    lum = (out[...,0]+out[...,1]+out[...,2])/3
    print(f'\nF={F}: perfil lunar (mediana lum×1000):')
    fl = lum.ravel()
    prev=None; mono=True
    for a,b in [(440,470),(470,500),(500,530),(530,560),(560,600),(600,650)]:
        s=(r_ll.ravel()>=a)&(r_ll.ravel()<b)
        m=np.median(fl[s])*1000
        if prev is not None and m < prev - 1.0: mono=False
        print(f'  r_ll {a}-{b}: {m:6.1f}')
        prev=m
    print('  creixent fins al pic i sense vall?', mono)
    del lift, out, lum
