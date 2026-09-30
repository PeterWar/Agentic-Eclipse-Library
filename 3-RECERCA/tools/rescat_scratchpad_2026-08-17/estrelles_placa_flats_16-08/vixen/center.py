import rawpy, numpy as np
from scipy import ndimage as ndi
DIR='/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/'
def g1(f):
    r=rawpy.imread(DIR+f+'.CR3'); im=r.raw_image_visible[:4638,:6958].astype(np.float64); r.close()
    return im[0::2,1::2]-511.5   # G1 (row even, col odd)
for f,ex in [('572A2971',0.125),('572A3001',0.125),('572A2977',0.25),('572A2995',0.25),('572A2969',0.008),('572A2987',0.008)]:
    a=g1(f)
    # threshold: use a level well above sky
    lo=np.percentile(a,20); hi=np.percentile(a,99.9)
    T=lo+0.06*(hi-lo)
    B=a>T
    B=ndi.binary_closing(B,np.ones((5,5)))
    F=ndi.binary_fill_holes(B)
    holes=F&~B
    lab,n=ndi.label(holes)
    if n==0: print(f,'no hole'); continue
    sizes=ndi.sum(holes,lab,range(1,n+1))
    k=int(np.argmax(sizes))+1
    m=lab==k
    ys,xs=np.nonzero(m)
    cy,cx=ys.mean(),xs.mean(); area=m.sum(); rad=np.sqrt(area/np.pi)
    # full-res coords: x_full = 2*xs+1, y_full=2*ys
    print(f, 'T=%.0f'%T, 'hole px',area, 'cx_half %.2f cy_half %.2f r_half %.2f'%(cx,cy,rad),
          '-> full cx %.2f cy %.2f r %.2f  (r arcsec %.1f)'%(2*cx+1,2*cy,2*rad,2*rad*2.158))
