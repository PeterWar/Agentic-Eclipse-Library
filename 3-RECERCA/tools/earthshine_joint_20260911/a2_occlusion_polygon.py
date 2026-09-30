"""Integrate the supplied observed limb by exact polygon/pixel intersection.
Refine only the angular representation of the supplied piecewise-linear radius
until the forward prediction converges. This changes no source image or PSB.
The true optical/terrain boundary remains uncertain independently of numerics.
"""
from joint_common import *
from scipy.fft import dctn,idctn
import time

def clip(a,axis,bound,above):
    if not len(a):return a
    b=np.roll(a,1,axis=0);inside=(a[:,axis]>=bound) if above else (a[:,axis]<=bound);prev=np.roll(inside,1);cross=inside!=prev
    counts=inside.astype(int)+cross.astype(int);offset=np.cumsum(counts)-counts;out=np.empty((int(counts.sum()),2))
    c=cross.nonzero()[0]
    if len(c):
        u=(bound-b[c,axis])/(a[c,axis]-b[c,axis]);out[offset[c]]=b[c]+u[:,None]*(a[c]-b[c])
    c=inside.nonzero()[0];out[offset[c]+cross[c].astype(int)]=a[c]
    return out

def pixel_area(p):
    for axis,bound,above in [(0,-.5,True),(0,.5,False),(1,-.5,True),(1,.5,False)]:p=clip(p,axis,bound,above)
    if len(p)<3:return 0.
    return abs(float(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))))*.5

# Independent elementary geometries qualify the area integrator.
assert abs(pixel_area(np.array([[-1.,-1],[1,-1],[1,1],[-1,1]]))-1)<1e-14
assert abs(pixel_area(np.array([[0.,-1],[1,-1],[1,1],[0,1]]))-.5)<1e-14
assert abs(pixel_area(np.array([[-.5,-.5],[.5,-.5],[-.5,.5]]))-.5)<1e-14
assert pixel_area(np.array([[2.,2],[3,2],[3,3],[2,3]]))==0

edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');K=len(edge)
y,x=np.mgrid[:N,:N];xx=x-CX;yy=y-CY;theta=np.arctan2(yy,xx);rad=np.hypot(xx,yy);t=(theta%(2*np.pi))*K/(2*np.pi);ii=np.floor(t).astype(int);u=t-ii;rr=edge[ii]*(1-u)+edge[(ii+1)%K]*u
band=abs(rr-rad)<3;bx=xx[band];by=yy[band];bt=theta[band]
corners=np.array([[-.5,-.5],[-.5,.5],[.5,-.5],[.5,.5]])
corner_angle=np.arctan2(by[:,None]+corners[:,1],bx[:,None]+corners[:,0]);rel=(corner_angle-bt[:,None]+np.pi)%(2*np.pi)-np.pi
amin=bt+rel.min(axis=1);amax=bt+rel.max(axis=1)

def integrate(refine):
    p=(rad<rr).astype(float);step=2*np.pi/(K*refine);vals=[]
    for a,b,lo,hi in zip(bx,by,amin,amax):
        j=np.arange(int(np.floor(lo/step))-1,int(np.ceil(hi/step))+2)
        angles=j*step;t=(j%(K*refine))/refine;ii=np.floor(t).astype(int);u=t-ii;R=edge[ii]*(1-u)+edge[(ii+1)%K]*u
        arc=np.stack([R*np.cos(angles)-a,R*np.sin(angles)-b],axis=1)
        poly=np.concatenate([np.array([[-a,-b]]),arc])
        vals.append(pixel_area(poly))
    p[band]=vals;assert p.min()>=0 and p.max()<=1+1e-12
    return p

start=time.time();P4=integrate(4);print('POLYGON4',time.time()-start,flush=True)
P16=integrate(16);print('POLYGON16',time.time()-start,flush=True)
P64=integrate(64);print('POLYGON64',time.time()-start,flush=True)
sigma=np.sqrt(1.5140726846997261**2-1/12);f=np.arange(N)/(2*N);H=np.exp(-2*np.pi**2*sigma**2*(f[:,None]**2+f[None,:]**2))
conv=lambda a:idctn(dctn(a,type=2,norm='ortho')*H,type=2,norm='ortho')
z=np.load(OUT/'A1_occlusion_area.npz');checks=[]
for name,p in [('quadrature4',z['P4']),('quadrature128',z['P128']),('polygon4',P4),('polygon16',P16)]:
    d=p-P64;pred=conv(d)*(500-100000)
    checks.append(dict(method=name,pixel_area_abs_error_quantiles=np.percentile(abs(d[band]),[50,90,99,100]).tolist(),constant_step_prediction_error_G_quantiles=np.percentile(abs(pred[abs(rad-rr)<8]),[50,90,99,100]).tolist()))
assert checks[-1]['constant_step_prediction_error_G_quantiles'][-1]<1.,checks[-1]
np.savez_compressed(OUT/'A2_occlusion_polygon.npz',P4=P4,P16=P16,P64=P64)
save('A2_occlusion_polygon.json',dict(method=__doc__,seconds=time.time()-start,elementary_area_tests_PASS=True,convergence_PASS=True,checks=checks,selected='P64',limits=['Exact polygon intersection of a refined representation of the observed radial edge','Numerical convergence does not validate that optical edge as the true opaque limb','Fixed1400 source grid; no FOV, photographic mask, RAW or Photoshop change']))
print(json.dumps(checks,indent=2),flush=True)
