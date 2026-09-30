"""Acaba les màscares de 04_1-2s i 03_1s de la V5 (ordre de Pere, 20-08 matinada): protecció de
protuberàncies, vora lunar i perles, multiplicada sobre la màscara existent, amb desenfoc gaussià.
Recompon l'interior i verifica: (a) compositor == compost del xat V4 amb màscares originals;
(b) amb les acabades, les zones sagrades = capes de sota; (c) cap anell nou centrat a la Lluna."""
import os, json, numpy as np
from scipy.ndimage import gaussian_filter
D = os.path.dirname(os.path.abspath(__file__)); V5D = os.path.join(D,'v5')
W,H = 7648,5353
SOL = (4020.89,2737.66); R_SOL = 446.15   # coords V5
LLUNA = (4034.8,2736.3); PROT = (3578,2653)
yy,xx = np.mgrid[0:H,0:W].astype(np.float32)
r_ll = np.hypot(xx-LLUNA[0],yy-LLUNA[1])
def sstep(t):
    t=np.clip(t,0,1); return t*t*t*(t*(t*6-15)+10)
# proteccions: anell del limbe (ple fins a 495 px, rampa 50) + el·lipse de la protuberància (130x150, rampa ~45)
P_limb = sstep((540.0 - r_ll)/70.0)
e = np.sqrt(((xx-PROT[0])/70.0)**2 + ((yy-PROT[1])/100.0)**2)
P_prot = sstep((1.35 - e)/0.35)
P = np.maximum(P_limb, P_prot)
P = gaussian_filter(P, 8.0)
np.save(os.path.join(D,'proteccio_P.npy'), P.astype(np.float32))
meta = json.load(open(os.path.join(V5D,'meta.json')))
def mask_canvas(i, m):
    mk = m.get('mask')
    if mk is None: return np.ones((H,W),np.float32)
    mask = np.load(os.path.join(V5D,f'v{i:02d}_mask.npy')).astype(np.float32)/65535.0
    mfull = np.full((H,W), mk['bg']/255.0, np.float32)
    dy0,dx0 = max(0,mk['top']), max(0,mk['left'])
    hh = min(mk['bottom'],H)-dy0; ww = min(mk['right'],W)-dx0
    mfull[dy0:dy0+hh, dx0:dx0+ww] = mask[max(0,-mk['top']):max(0,-mk['top'])+hh, max(0,-mk['left']):max(0,-mk['left'])+ww]
    return mfull
def compose(mask_over=None):
    comp = np.zeros((H,W,3),np.float32)
    for m in meta:
        if not m['visible']: continue
        i = m['i']
        rgb = np.load(os.path.join(V5D,f'v{i:02d}_rgb.npy')).astype(np.float32)/65535.0
        s = np.zeros((H,W,3),np.float32); cov = np.zeros((H,W),np.float32)
        dy0,dx0 = max(0,m['top']), max(0,m['left'])
        sy0,sx0 = max(0,-m['top']), max(0,-m['left'])
        hh = min(m['bottom'],H)-dy0; ww = min(m['right'],W)-dx0
        s[dy0:dy0+hh,dx0:dx0+ww] = rgb[sy0:sy0+hh,sx0:sx0+ww]
        cov[dy0:dy0+hh,dx0:dx0+ww] = 1.0
        a = mask_canvas(i, m)
        if mask_over is not None and i in mask_over:
            a = a * mask_over[i]
        a = a * cov * (m['opacity']/255.0)
        comp = comp*(1.0-a[...,None]) + s*a[...,None]
        del rgb, s, cov, a
    return comp
print('composant amb màscares ORIGINALS…', flush=True)
c0 = compose()
ref = np.load('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/47c293ed-2e8a-4c78-a543-00c84f771077/scratchpad/v5out/compost_rgb16.npy', mmap_mode='r')
d = np.abs(c0 - np.asarray(ref,np.float32)/65535.0)
print('validació compositor vs xat V4: mediana', float(np.median(d))*65535, 'p99', float(np.percentile(d,99))*65535, 'màx', float(d.max())*65535, '(u16)')
print('composant amb màscares ACABADES…', flush=True)
mo = {10: (1.0-P), 11: (1.0-P)}
c1 = compose(mask_over=mo)
np.save(os.path.join(D,'v5fix_compost.npy'), np.clip(np.rint(c1*65535),0,65535).astype(np.uint16))
# efecte per zones
th_ll = np.degrees(np.arctan2(yy-LLUNA[1], xx-LLUNA[0]))
r_sun = np.hypot(xx-SOL[0],yy-SOL[1])/R_SOL
zones = {
 'protuberancia': (((xx-PROT[0])/140.0)**2+((yy-PROT[1])/160.0)**2)<1.0,
 'limbe 445-465': (r_ll>=445)&(r_ll<465),
 'limbe 465-500': (r_ll>=465)&(r_ll<500),
 'perles E': (r_sun>=0.95)&(r_sun<1.05)&(np.abs(th_ll)<60),
}
print('\ncanvi del compost amb la protecció (mediana |dif| u16 / p99):')
for nz, sel in zones.items():
    dd = np.abs(c1[sel]-c0[sel])*65535
    print(f'  {nz:16s} med {np.median(dd):7.1f}  p99 {np.percentile(dd,99):8.1f}')
# anell nou? mediana per anell centrat a la LLUNA, abans/després, a la corona (fora de la protuberància)
lum0=(c0[...,0]+c0[...,1]+c0[...,2])/3; lum1=(c1[...,0]+c1[...,1]+c1[...,2])/3
print('\nperfil centrat a la Lluna (mediana lum × 1000), abans → després:')
for a,b in [(440,470),(470,500),(500,530),(530,560),(560,600),(600,650),(650,720)]:
    sel=(r_ll>=a)&(r_ll<b)&(P_prot<0.05)
    print(f'  r_ll {a}-{b}: {np.median(lum0[sel])*1000:6.1f} → {np.median(lum1[sel])*1000:6.1f}')
