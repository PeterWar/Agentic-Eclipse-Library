"""Support-aware diagnostic Fourier functions; no implicit writes."""
from common import *
from scipy.ndimage import map_coordinates,distance_transform_edt
from scipy.fft import rfft2
NT=1440;RR=np.arange(60.,450.,.5);TH=np.arange(NT)*2*np.pi/NT
CO=[CY+RR[:,None]*np.sin(TH),CX+RR[:,None]*np.cos(TH)]
FREQ=np.fft.rfftfreq(NT)[None,:]*NT/(2*np.pi*RR[:,None])
def polar(a):
    valid=np.isfinite(a)
    if not valid.all():
        ix=distance_transform_edt(~valid,return_distances=False,return_indices=True);a=a[tuple(ix)]
    p=map_coordinates(a,CO,order=3,mode='nearest')
    v=map_coordinates(valid.astype(float),CO,order=1,mode='constant')>.999
    assert np.isfinite(p).all()
    return p,v
def angular_band(p,lo,hi):
    return np.fft.irfft(np.fft.rfft(p,axis=1)*((FREQ>=1/hi)&(FREQ<=1/lo)),n=NT,axis=1)
def sector_mask(lo,hi,parity):
    return (RR[:,None]>=lo)&(RR[:,None]<hi)&((np.arange(NT)[None,:]//120)%2==parity)
def tiles(n=192,step=96,maxradius=435):
    ans=[]
    for dy in range(-288,289,step):
        for dx in range(-288,289,step):
            if np.hypot(abs(dx)+n/2,abs(dy)+n/2)>maxradius:continue
            x0=int(round(CX+dx-n/2));y0=int(round(CY+dy-n/2));ans.append(dict(x0=x0,y0=y0,size=n,dx=dx,dy=dy,parity=(int(round(np.arctan2(dy,dx)%(2*np.pi)/(np.pi/6)))%12)%2))
    return ans
def tile_fft(a,tile):
    n=tile['size'];y0=tile['y0'];x0=tile['x0'];b=a[y0:y0+n,x0:x0+n].astype(float);assert np.isfinite(b).all()
    y,x=np.mgrid[:n,:n]/n;A=np.stack([np.ones_like(x),x,y],-1);w=np.hanning(n)[:,None]*np.hanning(n)[None,:]
    coef=np.linalg.lstsq(A.reshape(-1,3)*w.reshape(-1,1),b.ravel()*w.ravel(),rcond=None)[0]
    return rfft2((b-A@coef)*w)
def fft_stats(a,b,band,n=192):
    fy=np.fft.fftfreq(n)[:,None];fx=np.fft.rfftfreq(n)[None,:];fr=np.hypot(fx,fy);sel=(fr>=1/band[1])&(fr<=1/band[0])
    x=a[sel];y=b[sel];aa=np.vdot(x,x).real;bb=np.vdot(y,y).real;ab=np.vdot(x,y).real
    return float(ab/np.sqrt(max(aa*bb,1e-30))),float(aa),float(bb),float(ab)
