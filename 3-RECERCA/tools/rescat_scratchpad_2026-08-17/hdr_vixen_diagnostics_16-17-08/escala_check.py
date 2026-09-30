import numpy as np, cv2, json
from scipy.ndimage import gaussian_filter
from scipy.signal import fftconvolve
sk = np.load('sketch_q4.npy')[...,1]; fo = np.load('foto.npy')[...,1]
g = json.load(open('geom.json')); s = g['sketch_q4']
# high-pass del sketch
def hp(a, s1=2.0, s2=8.0):
    return gaussian_filter(a, s1) - gaussian_filter(a, s2)
skh = hp(sk)
cxs, cys = s['cx'], s['cy']
# retall del sketch al voltant del centre: 700 px de radi
Rc = 700
win_s = skh[int(cys)-Rc:int(cys)+Rc, int(cxs)-Rc:int(cxs)+Rc]
# màscara anular 1.2–3.2 R_sol (R_sol ≈ 249 q4)
yy, xx = np.mgrid[-Rc:Rc, -Rc:Rc]; rr = np.hypot(xx, yy)
mask = (rr > 1.2*249) & (rr < 3.2*249)
best = []
for fac in np.arange(0.52, 0.62, 0.005):
    f2 = cv2.resize(fo, None, fx=fac, fy=fac, interpolation=cv2.INTER_AREA)
    fh = hp(f2)
    cxf, cyf = 3439*fac, 2234*fac
    win_f = fh[int(round(cyf))-Rc:int(round(cyf))+Rc, int(round(cxf))-Rc:int(round(cxf))+Rc]
    if win_f.shape != win_s.shape: continue
    a = (win_s - win_s[mask].mean())*mask; b = (win_f - win_f[mask].mean())*mask
    # correlació creuada amb desplaçaments ±20 px
    cc = fftconvolve(a, b[::-1, ::-1], mode='same')
    c0 = cc.shape[0]//2
    sub = cc[c0-20:c0+21, c0-20:c0+21]
    k = np.unravel_index(np.argmax(sub), sub.shape)
    val = sub[k] / np.sqrt((a**2).sum()*(b**2).sum())
    best.append((fac, float(val), int(k[0]-20), int(k[1]-20)))
    print(f'fac {fac:.3f} corr {val:.4f} shift dy={k[0]-20} dx={k[1]-20}')
best.sort(key=lambda t: -t[1]); print('millor', best[:3])
