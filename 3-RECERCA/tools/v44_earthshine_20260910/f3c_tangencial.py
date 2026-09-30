"""Directional lunar detail: azimuthal Fourier operation at each fixed radius.
No radial mixing, so the bright exterior cannot leak into the inner annulus.
This is explicitly a tangential-detail derivative, not an isotropic recovery.
"""
from comu44 import *
from scipy.ndimage import gaussian_filter1d

def main():
    prepare();naz=4096;rr=np.arange(320.,456.,.5);th=np.arange(naz)*2*np.pi/naz
    mx=(CXT+rr[:,None]*np.cos(th)).astype(np.float32);my=(CYT+rr[:,None]*np.sin(th)).astype(np.float32)
    freq=np.fft.rfftfreq(naz)[None,:]*naz/(2*np.pi*rr[:,None])
    filt=(1-np.exp(-(freq*40)**8))*np.exp(-(freq*10.)**8)
    rep={'method':'log-G angular FFT at fixed r; no radial filter; physical lambda10/40 shoulders; directional only','groups':{}}
    for name in ('surface_clean','surface_vixen','surface_sonyA','surface_sonyB'):
        g=np.load(CAU44/f'{name}_rgb.npy')[...,1]
        p=cv2.remap(np.nan_to_num(g),mx,my,cv2.INTER_LINEAR)
        ln=np.log(np.maximum(p,1e-3));hf=np.fft.irfft(np.fft.rfft(ln,axis=1)*filt,n=naz,axis=1)
        # Local baseline amplitude is physical DN. Smooth angular background is auxiliary.
        low=np.fft.irfft(np.fft.rfft(ln,axis=1)*np.exp(-(freq*64)**8),n=naz,axis=1)
        d=(hf*np.exp(low)).astype(np.float32)
        mxx=((PHI%(2*np.pi))*naz/(2*np.pi)).astype(np.float32)
        myy=((R-rr[0])/.5).astype(np.float32)
        # Pad angular periodic boundary; radial samples outside the analysis strip are zero.
        dp=np.concatenate([d,d[:,:1]],axis=1)
        out=cv2.remap(dp,mxx,myy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        np.save(CAU44/f'{name}_detail_tangent.npy',out)
        np.save(CAU44/f'{name}_detail_tangent_polar.npy',d)
        rep['groups'][name]={str(c):float(np.std(out[(R>c*RL)&(R<(c+.01)*RL)])) for c in (.85,.90,.94,.96)}
        print(name,rep['groups'][name],flush=True)
    savejson(REB44/'F3c_tangencial.json',rep)

if __name__=='__main__':main()
