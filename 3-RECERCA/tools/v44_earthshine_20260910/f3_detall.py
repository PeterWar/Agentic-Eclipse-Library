"""Linear local background removal with overlap-add; no reference image input.
The transfer probe is separate and reports actual Fourier-band amplitudes.
"""
from comu44 import *
from scipy.ndimage import gaussian_filter, distance_transform_edt

def local_detail(z, size=64, stride=16, lam_low=6., lam_high=40.):
    z=np.asarray(z,dtype=float);bad=~np.isfinite(z)
    if bad.any():z=z[tuple(distance_transform_edt(bad,return_distances=False,return_indices=True))]
    # Padding is computational only, output grid is unchanged.
    pad=size;zp=np.pad(z,pad,mode='reflect');res=np.zeros_like(zp);den=np.zeros_like(zp)
    yy,xx=np.mgrid[:size,:size].astype(float);xx=(xx-(size-1)/2)/(size/2);yy=(yy-(size-1)/2)/(size/2)
    A=np.stack([np.ones_like(xx),xx,yy,xx*xx,xx*yy,yy*yy],-1).reshape(-1,6)
    h=np.sin(np.pi*(np.arange(size)+.5)/size)**2;win=h[:,None]*h[None,:]
    root=np.sqrt(win);pinv=np.linalg.solve(A.T@(win.ravel()[:,None]*A),A.T*win.ravel()[None,:])
    fy=np.fft.fftfreq(size);fx=np.fft.rfftfreq(size);freq=np.hypot(fy[:,None],fx[None,:])
    # Smooth Fourier shoulders; response measured rather than assumed.
    filt=(1-np.exp(-(freq*lam_high)**8))*np.exp(-(freq*lam_low)**8)
    for y in range(0,zp.shape[0]-size+1,stride):
        for x in range(0,zp.shape[1]-size+1,stride):
            sl=np.s_[y:y+size,x:x+size];q=zp[sl];r=q-(A@(pinv@q.ravel())).reshape(size,size)
            f=np.fft.irfft2(np.fft.rfft2(r*root)*filt,s=(size,size))*root
            res[sl]+=f;den[sl]+=win
    return (res/np.maximum(den,1e-12))[pad:pad+z.shape[0],pad:pad+z.shape[1]].astype(np.float32)

def probe():
    # The same operator is translation-variant at the patch stride; probe phases and orientations.
    n=256;y,x=np.mgrid[:n,:n];m=(x>64)&(x<n-64)&(y>64)&(y<n-64);rep=[]
    for lam in (8.,12.,16.,24.,32.):
        vals=[]
        for angle in (0.,np.pi/6,np.pi/3,np.pi/2):
            for phase in (0.,.7,1.4):
                s=np.sin(2*np.pi*(x*np.cos(angle)+y*np.sin(angle))/lam+phase)
                o=local_detail(s);vals.append(float(np.sum(s[m]*o[m])/np.sum(s[m]*s[m])))
        rep.append(dict(wavelength_px=lam,min=min(vals),max=max(vals),mean=float(np.mean(vals))))
    return rep

def main():
    prepare();rep={'operator':'weighted local quadratic 64px, stride16; sqrt-Hann Fourier OLA; smooth shoulders lambda6 and40','transfer':probe(),'sources':{}}
    for name in ('surface_clean','surface_vixen','surface_sonyA','surface_sonyB'):
        z=np.load(CAU44/f'{name}_rgb.npy')[...,1]
        d=local_detail(z);np.save(CAU44/f'{name}_detail.npy',d)
        rep['sources'][name]=dict(rms_inside=float(np.std(d[R<.7*RL])),rms_outer=float(np.std(d[(R>.85*RL)&(R<.90*RL)])))
        png(f'F3_{name}_detail.png',.5+d/30.)
        print(name,rep['sources'][name],flush=True)
    savejson(REB44/'F3_detall.json',rep);print('TRANSFER',rep['transfer'],flush=True)

if __name__=='__main__':main()
