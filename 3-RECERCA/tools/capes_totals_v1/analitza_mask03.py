"""Què fan les màscares de 03_1s i 04_1-2s de la V5 a les tres zones sagrades, i quant hi pinta cada capa."""
import numpy as np
from psd_tools import PSDImage
V5 = '/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/CapesInteriorsV5.psb'
W,H = 7648,5353; SOL=(4020.89,2737.66); R_SOL=446.15   # coords V4/V5 (digest §7.2)
LLUNA=(4034.8,2736.3); PROT=(3578,2653)
psd = PSDImage.open(V5)
layers = list(psd)
yy,xx = np.mgrid[0:H,0:W].astype(np.float32)
r = np.hypot(xx-SOL[0],yy-SOL[1])/R_SOL
r_ll = np.hypot(xx-LLUNA[0],yy-LLUNA[1])
th_ll = np.degrees(np.arctan2(yy-LLUNA[1], xx-LLUNA[0]))
zones = {
 'protuberancia (el·lipse 90x110+r50)': (((xx-PROT[0])/140.0)**2+((yy-PROT[1])/160.0)**2)<1.0,
 'dins Lluna (r_ll<430)': r_ll<430,
 'limbe anell (r_ll 445-465)': (r_ll>=445)&(r_ll<465),
 'limbe anell ample (r_ll 465-500)': (r_ll>=465)&(r_ll<500),
 'perles E (r 0,95-1,05, |th|<60)': (r>=0.95)&(r<1.05)&(np.abs(th_ll)<60),
}
for idx in (10, 11):
    l = layers[idx]; m = l.mask
    marr = l.numpy('mask')[...,0]
    mfull = np.full((H,W), m.background_color/255.0, np.float32)
    dy0,dx0 = max(0,m.top), max(0,m.left)
    hh = min(m.bottom,H)-dy0; ww = min(m.right,W)-dx0
    mfull[dy0:dy0+hh, dx0:dx0+ww] = marr[max(0,-m.top):max(0,-m.top)+hh, max(0,-m.left):max(0,-m.left)+ww]
    print(f"== {l.name}")
    for nz, sel in zones.items():
        v = mfull[sel]
        print(f"   {nz:38s} mitjana {v.mean():.3f}  p95 {np.percentile(v,95):.3f}  màx {v.max():.3f}")
    # perfil moon-centered de la màscara vora el limbe
    print("   perfil r_ll (mitjana): ", end="")
    for a,b in [(380,430),(430,450),(450,470),(470,500),(500,560),(560,650)]:
        sel=(r_ll>=a)&(r_ll<b); print(f"{a}-{b}:{mfull[sel].mean():.3f}", end="  ")
    print()
