import tifffile, numpy as np, json, sys
from scipy.ndimage import map_coordinates, rotate
N=320; HALF=1.05
def patch(path,cx,cy,R,rmax=0.70):
    a=tifffile.imread(path)[...,1].astype(np.float32)
    u=(np.arange(N)-(N-1)/2.0)*(2*HALF/N)
    yy,xx=np.meshgrid(u,u,indexing='ij')
    p=map_coordinates(a,[cy+yy*R,cx+xx*R],order=1,mode='nearest')
    r=np.hypot(yy,xx); m=r<rmax
    terms=[xx**i*yy**j for i in range(4) for j in range(4) if i+j<=3]
    A=np.stack([t[m] for t in terms],1); c,*_=np.linalg.lstsq(A,p[m],rcond=None)
    res=p-sum(k*t for k,t in zip(c,terms)); res=np.where(m,res-res[m].mean(),0.0)
    return res,m,float(np.median(p[m]))
def rho(a,b,m): return float((a[m]*b[m]).sum()/np.sqrt((a[m]**2).sum()*(b[m]**2).sum()))
cfg=json.loads(sys.argv[1]); P={c["tag"]:patch(c["path"],c["cx"],c["cy"],c["R"]) for c in cfg}
S1=P["SONY_anc1"][0]; S3=P["SONY_anc3"][0]; m=P["SONY_anc1"][1]
for vt in ["VIX_2983","VIX_2984","VIX_2982"]:
    V=P[vt][0]
    sc=[(rho(S1,rotate(V,a,reshape=False,order=1),m),a) for a in np.arange(-50,-10,1.0)]
    best=max(sc); print(f"S1 x {vt}: pic {best[0]:+.3f} a {best[1]:+.1f} deg")
    Vm=V[:, ::-1]     # control: parell invertit (mirall) -> cap rotacio fisica no ho pot fer
    scm=[(rho(S1,rotate(Vm,a,reshape=False,order=1),m),a) for a in np.arange(-180,180,2.0)]
    bm=max(scm); print(f"   control MIRALL sobre 360 deg: pic {bm[0]:+.3f} a {bm[1]:+.1f} deg")
    scn=[(rho(S1,rotate(V,a,reshape=False,order=1),m),a) for a in np.arange(-180,180,2.0)]
    arr=np.array([x[0] for x in scn]); print(f"   escombrada 360 deg no-mirall: max {arr.max():+.3f} min {arr.min():+.3f} sd {arr.std():.3f}")
print(f"\nS1 x S3 (mateix cos): {rho(S1,S3,m):+.3f}")
sc=[(rho(S3,rotate(P['VIX_2983'][0],a,reshape=False,order=1),m),a) for a in np.arange(-50,-10,1.0)]
print("S3 x VIX_2983: pic %+.3f a %+.1f deg"%max(sc))
