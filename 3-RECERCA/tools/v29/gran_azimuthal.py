"""Wide angular detail: no convolution or differentiation across radii.

Constant physical arc scales, exact periodic Gaussian Fourier convolution.
Polar samples are an internal evaluation grid; output/FOV stay unchanged.
The nonlinear display is applied only after returning to the existing grid.
"""
from common import *
from refine_detail import contrast_profile
from fuse_and_filter import layer

def angular(x,m,r,t):
    x=np.where(m,x,0).astype(np.float32);mf=m.astype(np.float32)
    r0=400;nr=int(np.ceil(r.max()))-r0+2;nt=16384;theta=np.arange(nt,dtype=np.float32)*2*np.pi/nt
    freq=np.fft.rfftfreq(nt)[None,:];p=np.empty((nr,nt),np.float32)
    for start in range(0,nr,64):
        rr=(r0+np.arange(start,min(start+64,nr),dtype=np.float32))[:,None]
        mx=(CX+rr*np.cos(theta)[None,:]).astype(np.float32);my=(CY+rr*np.sin(theta)[None,:]).astype(np.float32)
        wm=cv2.remap(mf,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        xp=cv2.remap(x,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        fx=np.fft.rfft(xp,axis=1);fw=np.fft.rfft(wm,axis=1);bands=[]
        for sigma in (8,32,64,128):
            sp=sigma*nt/(2*np.pi*rr);g=np.exp(-2*np.pi**2*sp**2*freq**2)
            den=np.fft.irfft(fw*g,n=nt,axis=1);num=np.fft.irfft(fx*g,n=nt,axis=1)
            bands.append(np.where(den>1e-5,num/np.maximum(den,1e-5),0).astype(np.float32))
        p[start:start+len(rr)]=bands[0]-(bands[1]+bands[2]+bands[3])/3
    # Wrap the angular axis explicitly; radial coordinate never wraps.
    extended=np.concatenate([p[:,-1:],p,p[:,:1]],axis=1)
    mx=(np.mod(t,2*np.pi)*nt/(2*np.pi)+1).astype(np.float32);my=(r-r0).astype(np.float32)
    return np.where(m,cv2.remap(extended,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT),0)

def main():
    r,t=coords();mv=np.load(CAU/'vixen_support.npy');ms=np.load(CAU/'sony_support.npy')
    v=np.load(CAU/'vixen_total.npy',mmap_mode='r')[...,1];s=np.load(CAU/'sony_corrected_total.npy',mmap_mode='r')[...,1]
    original_union=mv|ms;mv&=np.isfinite(v)&(v>0);ms&=np.isfinite(s)&(s>0);m=mv|ms
    np.save(CAU/'gran_support.npy',m)
    wv=(1-smooth(r/RS,2,2.65))*mv;wv=np.where(ms,wv,mv.astype(np.float32));ws=(1-wv)*ms
    d=np.zeros((H,W),np.float32);scale=np.zeros_like(d);profiles={}
    for tag,a,mask,weight in [('vixen',v,mv,wv),('sony',s,ms,ws)]:
        x=np.log(np.maximum(a,1e-8));band=angular(x,mask,r,t);np.save(CAU/f'angular_{tag}_raw.npy',band)
        sc,profile=contrast_profile(detrend(x,mask,r),mask,r);d+=weight*band;scale+=weight*sc;profiles[tag]=profile;log('angular '+tag)
    d=np.where(m,d/np.maximum(scale,.002),0)
    rep=layer(d,m,r,'gran');rep.update({'operator':'angular G8-(G32+G64+G128)/3; physical arc scales inpx, periodic Gaussian FFT; no deliberate radial filtering, bilinear interpolation only','channel':'G','invalid_G_excluded':int((original_union&~m).sum()),'polar_grid':{'r0':400,'radial_step_px':1,'angles':16384},'post_contrast_profiles':profiles,'source':'each train filtered separately before blend; SonyB primary; no rho; separate normalized supports'})
    savejson(CAU/'gran_azimuthal_receipt.json',rep);log('angular wide ready')

if __name__=='__main__':main()
