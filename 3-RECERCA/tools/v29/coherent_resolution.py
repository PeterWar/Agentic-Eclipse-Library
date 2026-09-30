"""Choose resolution from independent Fourier-band coherence, not radius.

The finest detected coherent band sets a Gaussian-transfer cap of 0.90 at
its shortest wavelength. If no band is demonstrated, retain a conservative
8 px resolution and report that limit; no region is neutralized.
"""
from common import *
from PIL import Image

def main():
    E=np.load(CAU/'sony_even_total.npy',mmap_mode='r');O=np.load(CAU/'sony_odd_total.npy',mmap_mode='r')
    A=np.load(CAU/'sony_A_total.npy',mmap_mode='r');B=np.load(CAU/'sony_B_total.npy',mmap_mode='r')
    n=512;step=384;bands=[(8,16),(16,32),(32,64),(64,128),(128,256)]
    fr=np.hypot(np.fft.fftfreq(n)[:,None],np.fft.rfftfreq(n)[None,:]);masks=[(fr>=1/b)&(fr<1/a) for a,b in bands]
    win=np.outer(np.hanning(n),np.hanning(n)); ys=list(range(0,H-n+1,step));xs=list(range(0,W-n+1,step))
    grid=np.full((len(ys),len(xs)),8,np.float32);recs=[]
    def fft(z):
        z=np.log(np.maximum(z,1e-10));z=z-np.mean(z);return np.fft.rfft2(z*win)
    def corr(a,b,mask):
        av=a[mask];bv=b[mask];den=np.sqrt(np.sum(np.abs(av)**2)*np.sum(np.abs(bv)**2))
        return float(np.real(np.vdot(av,bv))/max(den,1e-30))
    for iy,y in enumerate(ys):
        for ix,x in enumerate(xs):
            sl=(slice(y,y+n),slice(x,x+n),1);ee=E[sl];oo=O[sl];aa=A[sl];bb=B[sl]
            valid=np.isfinite(ee)&np.isfinite(oo)&(ee>0)&(oo>0)
            if valid.mean()<.995:continue
            fe,fo=fft(ee),fft(oo);fa=fb=None
            cross=np.all(np.isfinite(aa)&np.isfinite(bb)&(aa>0)&(bb>0))
            if cross:fa,fb=fft(aa),fft(bb)
            row={'xy':[x+n/2,y+n/2],'independent_pointings':bool(cross),'bands':[]}; selected=None
            for (lo,hi),mask in zip(bands,masks):
                ce=corr(fe,fo,mask);ca=corr(fa,fb,mask) if cross else None
                # Null rotates phase by a quarter-window spatial shift.
                phase=np.exp(2j*np.pi*np.fft.rfftfreq(n)[None,:]*(n/4))
                null=corr(fe,fo*phase,mask)
                threshold=max(.12,null+.10)
                passes=ce>threshold and (not cross or ca>.12)
                row['bands'].append({'wavelength_px':[lo,hi],'temporal':ce,'pointing':ca,'null':null,'detected':bool(passes)})
                if passes and selected is None:selected=lo
            if selected is not None:grid[iy,ix]=min(8,.073058*selected)
            row['sigma_cap']=float(grid[iy,ix]);recs.append(row)
        log(f'coherence row {iy+1}/{len(ys)}')
    # Bilinear interpolation of caps is continuous. A local minimum expansion
    # preserves a fine structure approaching a tile boundary conservatively.
    conservative=cv2.erode(grid,np.ones((3,3),np.uint8))
    full=cv2.resize(conservative,(W,H),interpolation=cv2.INTER_LINEAR)
    # Vixen/inner blend is separately calibrated; the user gains all temporal
    # limb pixels and retains its fine resolution instead of importing Sony's.
    r,_=coords();sw=smooth(r/RS,2,2.65);full=(1-sw)*.7+sw*full
    np.save(CAU/'resolution_sigma.npy',full)
    savejson(CAU/'coherent_resolution.json',{'bands':bands,'tile_px':n,'stride_px':step,'cap_rule':'sigma<=0.073058*shortest demonstrated wavelength; 8px if none; no radial exclusion','tiles':recs,'grid_sigma':grid})
    Image.fromarray(np.round(np.clip(full[::4,::4]/8,0,1)*255).astype(np.uint8)).save(OUT/'QA_resolucio_adaptativa_llenc_comu_sencer.png')
    log('resolution map ready')

if __name__=='__main__':main()
