import numpy as np, pickle, rawpy
from scipy import ndimage
D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
P=pickle.load(open("peaks.pkl","rb")); names=list(P.keys())
# --- lunar disc centre: the dark disc inside the corona ---
cent={}
for n in names:
    bkg=np.load(f"bkg_{n}.npy")
    sm=ndimage.zoom(bkg,0.125,order=1)
    # the moon is the local minimum surrounded by the bright corona ring
    thr=np.percentile(sm,99.0)
    ring=sm>thr
    lab,_=ndimage.label(ring)
    sz=np.bincount(lab.ravel()); sz[0]=0
    big=(lab==sz.argmax())
    fill=ndimage.binary_fill_holes(big)
    ys,xs=np.nonzero(fill)
    cy,cx=ys.mean()*8,xs.mean()*8
    # refine: centroid of the "hole" (moon) inside
    hole=fill&~big
    if hole.sum()>50:
        ys,xs=np.nonzero(hole); cy,cx=ys.mean()*8,xs.mean()*8
    cent[n]=(cx,cy); print(f"{n} centre ~ ({cx:7.1f},{cy:7.1f})  disc_px~{hole.sum()*64}")
pickle.dump(cent,open("centres.pkl","wb"))

REF='DSC06993'
def offset(a,b,prior,W=70,nmax=2600):
    ia=np.argsort(-P[a]['snr'])[:nmax]; ib=np.argsort(-P[b]['snr'])[:nmax]
    dx=(P[b]['x'][ib][None,:]-P[a]['x'][ia][:,None]).ravel()
    dy=(P[b]['y'][ib][None,:]-P[a]['y'][ia][:,None]).ravel()
    k=(np.abs(dx-prior[0])<W)&(np.abs(dy-prior[1])<W); dx,dy=dx[k],dy[k]
    if len(dx)<10: return None
    b1=np.arange(prior[0]-W,prior[0]+W+1,1.0); b2=np.arange(prior[1]-W,prior[1]+W+1,1.0)
    H,ex,ey=np.histogram2d(dx,dy,bins=[b1,b2])
    Hs=ndimage.uniform_filter(H,3)*9
    i,j=np.unravel_index(np.argmax(Hs),Hs.shape)
    cx,cy=(ex[i]+ex[i+1])/2,(ey[j]+ey[j+1])/2
    k2=(np.abs(dx-cx)<2.5)&(np.abs(dy-cy)<2.5)
    exp_bg=len(dx)/(2*W)**2*np.pi*2.5**2
    return np.median(dx[k2]),np.median(dy[k2]),int(k2.sum()),exp_bg
print(f"\n{'frame':10s}{'exp':>5s} {'dx':>9s}{'dy':>9s} {'matched':>8s}{'expected':>9s}{'excess_sig':>11s}")
OFF={}
for n in names:
    if n==REF: OFF[n]=(0.0,0.0); print(f"{n:10s}{P[n]['exp']:5.0f} {0.0:9.2f}{0.0:9.2f}   reference"); continue
    pr=(cent[n][0]-cent[REF][0], cent[n][1]-cent[REF][1])
    r=offset(REF,n,pr)
    dx,dy,m,e=r; OFF[n]=(dx,dy)
    print(f"{n:10s}{P[n]['exp']:5.0f} {dx:9.2f}{dy:9.2f} {m:8d}{e:9.1f}{(m-e)/np.sqrt(e):11.1f}")
pickle.dump(OFF,open("offsets.pkl","wb"))
