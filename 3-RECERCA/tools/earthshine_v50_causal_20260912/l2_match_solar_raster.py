"""Read-only image-derived registration of pretransform Pere09 to current09.
Use coronal structure well outside the Moon; reserve alternating sectors and
the entire limb. No source image or Photoshop document is changed.
"""
from common50 import *
from scipy.ndimage import gaussian_filter,map_coordinates
from scipy.optimize import least_squares
from scipy.fft import fft,ifft
import time
srcpath=ROOT/'research/tools/capes_totals_v14/cau_v13pere/rgb_09.npy';raw=np.load(srcpath,mmap_mode='r');source=raw[...,1].astype(float)
target=np.load(OUT/'L1_current09_G16.npy').astype(float);geo=json.loads((OUT/'L1_current09_geometry.json').read_text());tc=np.array(geo['solar_xy'])-geo['origin_xy'];sc=np.array([3563.8912793889317,2274.660453669])
def feature(g):
 z=np.log(np.maximum(g,10));return gaussian_filter(z,2)-gaussian_filter(z,16)
S=feature(source);T=feature(target);th=np.arange(1440)*2*np.pi/1440;rr=np.arange(600,1100,2)
def polar(a,c):return map_coordinates(a,[c[1]+np.sin(th[:,None])*rr,c[0]+np.cos(th[:,None])*rr],order=1,mode='nearest')
ps=polar(S,sc);pt=polar(T,tc)
ps/=np.maximum(np.std(ps,axis=0),1e-6);pt/=np.maximum(np.std(pt,axis=0),1e-6)
curve=ifft(np.sum(np.conj(fft(pt,axis=0))*fft(ps,axis=0),axis=1)).real
lag=int(np.argmax(curve));lag=lag if lag<720 else lag-1440
y,x=np.mgrid[0:2600:6,0:2600:6];r=np.hypot(x-tc[0],y-tc[1]);a=np.arctan2(y-tc[1],x-tc[0])%(2*np.pi);ok=(r>550)&(r<1150);x=x[ok].astype(float);y=y[ok].astype(float);a=a[ok];truth=map_coordinates(T,[y,x],order=1);sector=np.floor(a/(np.pi/12)).astype(int);train=sector%2==0;test=~train
def norm(a):return (a-a.mean())/max(a.std(),1e-12)
def sample(p):
 an=np.deg2rad(p[0]);dx=x-tc[0]-p[1];dy=y-tc[1]-p[2];xx=sc[0]+(np.cos(an)*dx+np.sin(an)*dy)/p[3];yy=sc[1]+(-np.sin(an)*dx+np.cos(an)*dy)/p[3];return map_coordinates(S,[yy,xx],order=1,mode='nearest')
candidates=[np.array([v,0.,0.,1.]) for v in [lag*.25,-lag*.25]];init=min(candidates,key=lambda p:np.mean((norm(sample(p)[train])-norm(truth[train]))**2));start=time.time()
fit=least_squares(lambda p:norm(sample(p)[train])-norm(truth[train]),init,bounds=([init[0]-2,-30,-30,.97],[init[0]+2,30,30,1.03]),x_scale=[1,10,10,.01],diff_step=[1e-4,1e-3,1e-3,1e-5],max_nfev=160)
pred=sample(fit.x);report=dict(method=__doc__,source=str(srcpath),source_shape=list(source.shape),target_shape=list(target.shape),source_solar_center=sc.tolist(),target_solar_center=tc.tolist(),polar_lag=lag,initial=init.tolist(),parameters=dict(angle_deg=fit.x[0],dx=fit.x[1],dy=fit.x[2],scale=fit.x[3]),train_correlation=float(np.corrcoef(pred[train],truth[train])[0,1]),reserved_correlation=float(np.corrcoef(pred[test],truth[test])[0,1]),nfev=fit.nfev,success=bool(fit.success),seconds=time.time()-start,registration_scope='Pixel-raster lineage matching only; not independent astrometry or intrinsic edge truth')
sectors=[]
for k in range(24):
 use=sector==k;sectors.append(dict(sector=k,correlation=float(np.corrcoef(pred[use],truth[use])[0,1])))
report['sectors']=sectors;save('L2_solar_raster_alignment.json',report);print(json.dumps(report,indent=2),flush=True)
