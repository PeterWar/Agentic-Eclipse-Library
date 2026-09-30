"""Tests d'Opus (ronda 3): (1) sectors azimutals per anell 452-620; (2) rms del passa-alt (3-8 px) per anell 452-708.
Es corren sobre candidat, benchmark i V5fix4 (interior nu) per separar contingut d'artefacte."""
import numpy as np, tifffile
from scipy.ndimage import gaussian_filter
D='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/4df1ad91-85c7-4ede-b204-c1581f908873/scratchpad/ct1'
W,H=7648,5353; LLUNA=(4034.8,2736.3)
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
r_ll=np.hypot(xx-LLUNA[0],yy-LLUNA[1]); th=np.degrees(np.arctan2(yy-LLUNA[1],xx-LLUNA[0]))
imgs={'cand':np.load(f'{D}/compost_D_pont_135_195_trim.npy',mmap_mode='r'),
      'bench':tifffile.imread('/Users/USUARI/Downloads/Benchmark20Agost.tif'),
      'v5fix4':np.load(f'{D}/v5fix4.npy',mmap_mode='r')}
# --- test 1: desviació de sectors respecte de la mediana de l'anell
print('TEST 1 · pitjor sector (desviació % de la mediana d\'anell) per bandes d\'anelles:')
for nom,img in imgs.items():
    L=(np.asarray(img[...,0],np.float32)+np.asarray(img[...,1],np.float32)+np.asarray(img[...,2],np.float32))/(3*65535)
    pitjors=[]
    for a,b in [(452,494),(494,536),(536,578),(578,620)]:
        sel=(r_ll>=a)&(r_ll<b)
        med=np.median(L[sel]); devs=[]
        for a0 in range(-180,180,15):
            s=sel&(th>=a0)&(th<a0+15)
            if s.sum()>300: devs.append((np.median(L[s])-med)/med*100)
        pitjors.append(f'{a}-{b}: {min(devs):+5.1f}/{max(devs):+5.1f}%')
    print(f'  {nom:7s}', ' | '.join(pitjors))
# --- test 2: rms del passa-alt 3-8 px per anell
print('TEST 2 · rms passa-alt (DoG 3-8 px) per bandes (x1000): cand | bench | v5fix4  (cand≥90% bench?)')
hp={}
for nom,img in imgs.items():
    L=(np.asarray(img[...,0],np.float32)+np.asarray(img[...,1],np.float32)+np.asarray(img[...,2],np.float32))/(3*65535)
    hp[nom]=gaussian_filter(L,3.0)-gaussian_filter(L,8.0)
for a,b in [(452,494),(494,536),(536,578),(578,620),(620,708)]:
    sel=(r_ll>=a)&(r_ll<b)
    v=[float(np.sqrt(np.mean(hp[n][sel]**2)))*1000 for n in ('cand','bench','v5fix4')]
    print(f'  {a}-{b}: {v[0]:6.2f} | {v[1]:6.2f} | {v[2]:6.2f}   {"SÍ" if v[0]>=0.9*v[1] else "NO"} ({v[0]/max(v[1],1e-9)*100:.0f}%)')
