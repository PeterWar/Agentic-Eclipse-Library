import numpy as np, pickle
P=pickle.load(open("peaks.pkl","rb"))
names=list(P.keys())
REF='DSC06993'
def offset(a,b,R=1300,nmax=1200):
    ia=np.argsort(-P[a]['snr'])[:nmax]; ib=np.argsort(-P[b]['snr'])[:nmax]
    dx=(P[b]['x'][ib][None,:]-P[a]['x'][ia][:,None]).ravel()
    dy=(P[b]['y'][ib][None,:]-P[a]['y'][ia][:,None]).ravel()
    k=(np.abs(dx)<R)&(np.abs(dy)<R); dx,dy=dx[k],dy[k]
    H,ex,ey=np.histogram2d(dx,dy,bins=[np.arange(-R,R+2,2),np.arange(-R,R+2,2)])
    i,j=np.unravel_index(np.argmax(H),H.shape)
    cx,cy=(ex[i]+ex[i+1])/2,(ey[j]+ey[j+1])/2
    # refine
    k2=(np.abs(dx-cx)<4)&(np.abs(dy-cy)<4)
    return np.median(dx[k2]),np.median(dy[k2]),int(H[i,j]),int(k2.sum()),float(np.median(H[H>0]))
print(f"{'frame':10s} {'exp':>4s}  {'dx':>8s} {'dy':>8s}  {'hist_peak':>9s} {'matched':>7s} {'typical_bin':>11s}")
OFF={}
for n in names:
    if n==REF: OFF[n]=(0.0,0.0); print(f"{n:10s} {P[n]['exp']:4.0f}  {0.0:8.2f} {0.0:8.2f}   (reference)"); continue
    dx,dy,h,m,typ=offset(REF,n)
    OFF[n]=(dx,dy)
    print(f"{n:10s} {P[n]['exp']:4.0f}  {dx:8.2f} {dy:8.2f}  {h:9d} {m:7d} {typ:11.1f}")
pickle.dump(OFF,open("offsets.pkl","wb"))
