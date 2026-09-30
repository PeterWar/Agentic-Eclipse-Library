"""Solar spill estimator; output is a predicted additive optical component.

Preserve the original measurement and subtract only the estimated solar excess.
The lunar support is measured Vixen geometry, not a new Photoshop darkening
mask. A global plane estimated in the deep Moon supplies a reference level for
component separation only; it is not substituted for the observed lunar face.
"""
from common50 import *
from scipy.fft import dctn,idctn

def coordinates(z,upsample=1):
    h,w=z['g'].shape;u=(np.arange(w*upsample)+.5)/upsample-.5+int(z['u0']);v=(np.arange(h*upsample)+.5)/upsample-.5+int(z['v0'])
    nx=1+u[None,:]+v[:,None];ny=u[None,:]-v[:,None];J=z['native_to_world'];o=z['world_origin']
    return o[0]+J[0,0]*nx+J[0,1]*ny,o[1]+J[1,0]*nx+J[1,1]*ny

def transfer(shape,p,core,upsample=1):
    h,w=shape;fu=(np.arange(w*upsample)/(2*w))[None,:];fv=(np.arange(h*upsample)/(2*h))[:,None];f2=fu*fu+fv*fv
    T=np.full(f2.shape,1-p.sum())
    for coefficient,sigma in zip(p,SIGMA):T+=coefficient*np.exp(-np.pi**2*sigma*sigma*f2)
    T*=np.exp(-np.pi**2*core*core*f2)
    T*=np.sinc((fu+fv)/2)*np.sinc((fu-fv)/2)
    return T,f2

def estimate(g,z,p,core,regularization=.003,edge_shift=0.,upsample=3):
    assert upsample%2==1 and np.isfinite(g).all()
    x,y=coordinates(z);r=np.hypot(x-CX,y-CY);inside=r<350
    xx=(x-CX)/455;yy=(y-CY)/455
    A=np.stack([np.ones(inside.sum()),xx[inside],yy[inside]],1)
    b=np.linalg.lstsq(A,g[inside],rcond=None)[0];plane=b[0]+b[1]*xx+b[2]*yy
    Tg,f2=transfer(g.shape,p,core)
    F=dctn(g-plane,type=2,norm='ortho')
    # Smooth inverse regularization, identical over the entire rectangle.
    inv=Tg/(Tg*Tg+regularization*(4*f2)**2+1e-30)
    F*=inv;h,w=g.shape;Fu=np.zeros((h*upsample,w*upsample));Fu[:h,:w]=F*upsample
    intrinsic=idctn(Fu,type=2,norm='ortho');del Fu,F
    xu,yu=coordinates(z,upsample);theta=np.arctan2(yu-CY,xu-CX)%(2*np.pi)
    edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
    boundary=np.interp(theta,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi)+edge_shift
    exposed=np.hypot(xu-CX,yu-CY)>=boundary
    # The solar excess is nonnegative; no lunar texture is synthesized.
    solar=np.where(exposed,np.maximum(intrinsic,0),0);del intrinsic,xu,yu,theta,boundary,exposed
    T,_=transfer(g.shape,p,core,upsample)
    convolved=idctn(dctn(solar,type=2,norm='ortho')*T,type=2,norm='ortho');del solar,T
    # Odd supersampling puts original native green centres exactly on samples.
    spill=convolved[upsample//2::upsample,upsample//2::upsample].copy()
    return spill,dict(plane=b.tolist(),core=core,regularization=regularization,edge_shift=edge_shift,upsample=upsample,source_min=float(g.min()),corrected_min=float((g-spill).min()))
