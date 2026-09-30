import numpy as np, pickle
from scipy import ndimage
from scipy.spatial import cKDTree
OFF=pickle.load(open("offsets4.pkl","rb"))['off']
master=np.load("master_xy.npy").astype(float); msnr=np.load("master_snr.npy")
PK=pickle.load(open("peaks3.pkl","rb"))
moon=pickle.load(open("moon.pkl","rb")); RSUN=293.0
CX,CY=moon['DSC06993'][0],moon['DSC06993'][1]
EXP={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06988':1.0,
     'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
NEW={}
for n in EXP:
    P=PK[n]; dx0,dy0=OFF[n]
    cx,cy=CX+dx0,CY+dy0
    k=np.hypot(P['x']-cx,P['y']-cy)/RSUN>3.0
    px,py=P['x'][k],P['y'][k]
    W=35.0
    dx=(px[None,:]-master[:,0][:,None]).ravel(); dy=(py[None,:]-master[:,1][:,None]).ravel()
    s=(np.abs(dx-dx0)<W)&(np.abs(dy-dy0)<W); dx,dy=dx[s],dy[s]
    H,ex,ey=np.histogram2d(dx,dy,bins=[np.arange(dx0-W,dx0+W+1,1.0),np.arange(dy0-W,dy0+W+1,1.0)])
    Hs=ndimage.uniform_filter(H,3)*9
    i,j=np.unravel_index(np.argmax(Hs),Hs.shape)
    o=[(ex[i]+ex[i+1])/2,(ey[j]+ey[j+1])/2]
    for tol in (3.0,1.8):
        t=cKDTree(np.c_[px-o[0],py-o[1]]); d,idx=t.query(master,distance_upper_bound=tol)
        ok=np.isfinite(d)
        if ok.sum()<3: break
        a=px[idx[ok]]-master[ok,0]; b=py[idx[ok]]-master[ok,1]
        o=[float(np.median(a)),float(np.median(b))]
    NEW[n]=tuple(o)
    exp_rand=len(dx)/(2*W)**2*np.pi*1.8**2
    print(f"  {n} {EXP[n]:4.1f}s: dx={o[0]:+9.3f} dy={o[1]:+9.3f}  matched={ok.sum():3d}/{len(master)} (random~{exp_rand:.1f})"
          f"  rms=({np.std(a):.2f},{np.std(b):.2f})  delta_prev=({o[0]-dx0:+6.2f},{o[1]-dy0:+6.2f})")
pickle.dump({'off':NEW},open("offsets5.pkl","wb"))
