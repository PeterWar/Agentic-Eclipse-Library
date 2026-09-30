import rawpy, numpy as np
from scipy import ndimage as ndi
DIR='/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/'
# homogeneous set: all the 1/8 s (0.125) frames during totality
fs=[('572A2971',73735.29),('572A2989',73796.99),('572A3001',73809.80),('572A3007',73815.87)]
res=[]
for f,t in fs:
    r=rawpy.imread(DIR+f+'.CR3'); im=r.raw_image_visible[:4638,:6958].astype(np.float64); r.close()
    a=im[0::2,1::2]-511.5
    lo=np.percentile(a,20); hi=np.percentile(a,99.9); T=lo+0.06*(hi-lo)
    B=ndi.binary_closing(a>T,np.ones((5,5)))
    holes=ndi.binary_fill_holes(B)&~B
    lab,n=ndi.label(holes); s=ndi.sum(holes,lab,range(1,n+1)); m=lab==int(np.argmax(s))+1
    ys,xs=np.nonzero(m)
    res.append((t,2*xs.mean()+1,2*ys.mean(),2*np.sqrt(m.sum()/np.pi)))
    print('%s t=%.2f cx=%.3f cy=%.3f r=%.3f'%((f,)+res[-1]))
t=np.array([r[0] for r in res]); cx=np.array([r[1] for r in res]); cy=np.array([r[2] for r in res])
px=np.polyfit(t-t[0],cx,1); py=np.polyfit(t-t[0],cy,1)
print('moon in frame: vx=%.4f vy=%.4f px/s |v|=%.4f = %.3f arcsec/s ; resid %.2f/%.2f px'%(
    px[0],py[0],np.hypot(px[0],py[0]),np.hypot(px[0],py[0])*2.158,
    np.std(cx-np.polyval(px,t-t[0])),np.std(cy-np.polyval(py,t-t[0]))))
sx,sy=0.19993,-0.20017
dx,dy=px[0]-sx,py[0]-sy
print('Moon MINUS stars = Moon relative to Sun: (%.4f,%.4f) px/s -> %.4f px/s = %.3f arcsec/s (CLAUDE.md predicts 0.585)'%(dx,dy,np.hypot(dx,dy),np.hypot(dx,dy)*2.158))
print('angle between star drift and Moon-Sun motion: %.1f deg'%np.degrees(np.arccos((sx*dx+sy*dy)/np.hypot(sx,sy)/np.hypot(dx,dy))))
