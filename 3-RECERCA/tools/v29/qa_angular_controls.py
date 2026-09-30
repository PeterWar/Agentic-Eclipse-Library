"""Analytic angular transfer and radial-null controls for the FFT operator.

These validate the angular convolution, not an assertion that every texture
in a photograph is solar. Cartesian/polar interpolation remains a separate
declared approximation and is visually checked at the temporal limb.
"""
from common import *

def main():
    n=16384;th=np.arange(n)*2*np.pi/n;freq=np.fft.rfftfreq(n);out={'radial_null':[],'angular_transfer':[],'scope':'exact periodic normalized Gaussian core; interpolation inspected separately'}
    def filt(x,m,r):
        fx=np.fft.rfft(x*m);fm=np.fft.rfft(m);bs=[]
        for s in (8,32,64,128):
            g=np.exp(-2*np.pi**2*(s*n/(2*np.pi*r))**2*freq**2)
            den=np.fft.irfft(fm*g,n=n);num=np.fft.irfft(fx*g,n=n);bs.append(num/np.maximum(den,1e-8))
        return bs[0]-(bs[1]+bs[2]+bs[3])/3
    for R in (1.01,1.05,2,2.65,4,8,12):
        r=R*RS;m=(np.cos(th)>.15).astype(float);valid=m>0
        a=filt(np.full(n,8-np.log(R)*3),m,r);b=filt(np.full(n,10-np.log(R)*1.4),m,r)
        # Even an angularly varying blend cannot reintroduce different
        # radial gains after each train has independently yielded zero.
        w=(1+np.sin(th))/2;res=a*w+b*(1-w);err=float(np.max(np.abs(res[valid])))
        out['radial_null'].append({'R':R,'max_abs':err,'PASS':err<1e-10})
        for lam in (32,64,128,256):
            harmonic=max(1,round(2*np.pi*r/lam));x=np.sin(harmonic*th+.31);f=filt(x,np.ones(n),r)
            expected=np.exp(-.5*(harmonic*8/r)**2)-sum(np.exp(-.5*(harmonic*s/r)**2) for s in (32,64,128))/3
            measured=float(np.dot(f,x)/np.dot(x,x));ratio=measured/expected
            out['angular_transfer'].append({'R':R,'nominal_wavelength':lam,'measured':measured,'analytic':expected,'ratio':ratio,'PASS':abs(ratio-1)<1e-8})
    out['PASS']=all(z['PASS'] for k in ('radial_null','angular_transfer') for z in out[k]);assert out['PASS'];savejson(CAU/'angular_control_receipt.json',out);log('angular analytic controls PASS')

if __name__=='__main__':main()
