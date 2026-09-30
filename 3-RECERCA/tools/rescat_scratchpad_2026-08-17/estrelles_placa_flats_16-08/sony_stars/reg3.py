import numpy as np, pickle, rawpy
from scipy import ndimage
D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
P=pickle.load(open("peaks.pkl","rb")); names=sorted(P.keys())
# saturated-core centroid (robust, exposure-dependent but good to ~50 px)
CORE={}
for n in names:
    with rawpy.imread(D+n+".ARW") as r: v=r.raw_image_visible
    s=v>=16380; ys,xs=np.nonzero(s); CORE[n]=(xs.mean(),ys.mean())
REF='DSC06993'
def hist_offset(a,b,prior,W,binw=1.0,sm=3):
    xa,ya,sa=P[a]['x'],P[a]['y'],P[a]['snr']; xb,yb,sb=P[b]['x'],P[b]['y'],P[b]['snr']
    dx=(xb[None,:]-xa[:,None]).ravel(); dy=(yb[None,:]-ya[:,None]).ravel()
    k=(np.abs(dx-prior[0])<W)&(np.abs(dy-prior[1])<W); dx,dy=dx[k],dy[k]
    b1=np.arange(prior[0]-W,prior[0]+W+binw,binw); b2=np.arange(prior[1]-W,prior[1]+W+binw,binw)
    H,ex,ey=np.histogram2d(dx,dy,bins=[b1,b2])
    Hs=ndimage.uniform_filter(H,sm)*sm*sm
    i,j=np.unravel_index(np.argmax(Hs),Hs.shape)
    cx,cy=(ex[i]+ex[i+1])/2,(ey[j]+ey[j+1])/2
    k2=(np.abs(dx-cx)<2.0)&(np.abs(dy-cy)<2.0)
    dens=len(dx)/(2*W)**2                       # pairs per px^2 background
    exp_bg=dens*np.pi*2.0**2
    return np.median(dx[k2]),np.median(dy[k2]),int(k2.sum()),exp_bg,Hs.max(),np.median(Hs[Hs>0])
print(f"{'frame':10s}{'exp':>5s}{'prior_dx':>10s}{'prior_dy':>10s} | {'dx':>8s}{'dy':>8s}{'match':>7s}{'rand':>7s}{'sig':>7s}")
OFF={}; MATCH={}
for n in names:
    if n==REF: OFF[n]=(0.0,0.0); continue
    pr=(CORE[n][0]-CORE[REF][0],CORE[n][1]-CORE[REF][1])
    dx,dy,m,e,hm,hmed=hist_offset(REF,n,pr,90.0)
    OFF[n]=(dx,dy); MATCH[n]=(m,e)
    print(f"{n:10s}{P[n]['exp']:5.0f}{pr[0]:10.1f}{pr[1]:10.1f} | {dx:8.2f}{dy:8.2f}{m:7d}{e:7.1f}{(m-e)/np.sqrt(e):7.1f}")
OFF[REF]=(0.0,0.0)
pickle.dump({'off':OFF,'core':CORE},open("offsets.pkl","wb"))
