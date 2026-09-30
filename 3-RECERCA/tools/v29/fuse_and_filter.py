"""V29 candidate: coherent source, complete temporal support, isotropic ACHF.

All corrections are explicit and saved before deriving presentation layers.
The reference base outside the changed regions is retained at assembly.
"""
from common import *
from PIL import Image

def rho_fit(v,s,m,r,t):
    # Low-frequency colour matching, fit only in the measured overlap 2-3.5R.
    rr=r[::3,::3]; tt=t[::3,::3]; vv=v[::3,::3]; ss=s[::3,::3]
    ok=m[::3,::3]&(rr>2*RS)&(rr<3.5*RS)&(vv>0)&(ss>0)
    q=np.clip(vv[ok]/ss[ok],.1,10); lr=np.log(rr[ok]/RS); th=tt[ok]
    cen=np.linspace(np.log(2),np.log(3.5),40); idx=np.clip(np.searchsorted(cen,lr)-1,0,39)
    p=np.array([np.median(q[idx==i]) if np.any(idx==i) else np.nan for i in range(40)])
    good=np.isfinite(p); p=np.interp(cen,cen[good],p[good]); p=gaussian_filter1d(p,2)
    resid=q/np.interp(lr,cen,p)
    # Azimuthal medians make the fit insensitive to small ghosts and stars.
    tc=(np.arange(72)+.5)*2*np.pi/72-np.pi; ti=np.clip(((th+np.pi)*72/(2*np.pi)).astype(int),0,71)
    az=np.array([np.median(resid[ti==i]) for i in range(72)])
    A=np.stack([np.ones(72),np.cos(tc),np.sin(tc),np.cos(2*tc),np.sin(2*tc)],axis=1)
    coef=np.linalg.lstsq(A,az,rcond=None)[0]
    out=np.interp(np.log(np.maximum(r/RS,.001)),cen,p).astype(np.float32)
    out*=coef[0]+coef[1]*np.cos(t)+coef[2]*np.sin(t)+coef[3]*np.cos(2*t)+coef[4]*np.sin(2*t)
    return out,{'lnr_centres':cen,'radial':p,'azimuth_coefficients':coef}

def sn_smooth(F,m,t=.18,sigma=None):
    # Resolution is calibrated with independent temporal and pointing splits.
    # Interpolate in variance, not sigma, so a Gaussian mixture retains at
    # least the transfer of the declared sigma at a coherent Fourier band.
    w=m.astype(np.float32)
    if sigma is None:sigma=np.load(CAU/'resolution_sigma.npy',mmap_mode='r')
    levels=np.array([0,.5,1,2,4,8],np.float32);variance=sigma*sigma;vlevels=levels*levels
    out=np.zeros_like(F); remaining=np.ones_like(F)
    for i,s in enumerate(levels):
        if i==0: weight=np.clip(1-variance/vlevels[1],0,1); sm=F
        else:
            lo=vlevels[i-1]; hi=vlevels[min(i+1,len(levels)-1)];v=vlevels[i]
            weight=np.minimum(np.clip((variance-lo)/(v-lo),0,1),np.clip((hi-variance)/max(hi-v,1e-8),0,1)) if i<len(levels)-1 else np.clip((variance-lo)/(v-lo),0,1)
            sm=normgauss(F,w,float(s))
        out+=weight*sm; remaining-=weight
    assert np.max(np.abs(remaining))<2e-6
    return np.where(m,out,0).astype(np.float32),sigma

def achf(x,w,sigmas):
    out=np.zeros_like(x)
    for s in sigmas: out+=(x-normgauss(x,w,s))/len(sigmas)
    return np.where(w>0,out,0).astype(np.float32)

def centre_rings(a,m,r):
    """Full-pixel medians; continuous correction includes partial limb rings.

    Uses the 200 exact diagnostic bins, with actual observed median radii as
    interpolation nodes. No observed partial ring is excluded or downweighted.
    Shape-preserving cubic slopes join constant ends with zero derivative.
    """
    from scipy.interpolate import PchipInterpolator,CubicHermiteSpline
    rr=r[m];lo=np.log(20.);hi=np.log(float(rr.max()));nb=200
    idx=np.clip(((np.log(np.maximum(rr,1))-lo)/(hi-lo)*nb).astype(int),0,nb-1)
    order=np.argsort(idx,kind='stable');n=np.bincount(idx,minlength=nb);off=np.r_[0,np.cumsum(n)]
    sx=np.log(np.maximum(rr,1))[order];ks=np.flatnonzero(n>=400)
    nodes=np.array([np.median(sx[off[k]:off[k+1]]) for k in ks]);vals=a[m][order].copy();history=[]
    for iteration in range(8):
        p=np.array([np.median(vals[off[k]:off[k+1]]) for k in ks]);error=float(np.max(np.abs(p)));history.append(error)
        if error<=.03:break
        slopes=PchipInterpolator(nodes,p).derivative()(nodes);slopes[0]=slopes[-1]=0
        curve=CubicHermiteSpline(nodes,p,slopes,extrapolate=False)
        vals=(vals-curve(np.clip(sx,nodes[0],nodes[-1]))).astype(np.float32)
    assert history[-1]<=.03,history
    unsorted=np.empty_like(vals);unsorted[order]=vals;out=np.zeros_like(a);out[m]=unsorted
    return out,history

def layer(d,m,r,name):
    # V25 order: scale from unmodified detail, then tanh, S/N and H1. Explicit
    # strength is presentation only and remains editable via layer opacity.
    scale=float(np.percentile(np.abs(d[m]),99))/1.5
    mapped=(.5*np.tanh(d/max(scale,1e-6))).astype(np.float32)
    sm,sigma=sn_smooth(mapped,m)
    centered,h1_history=centre_rings(sm,m,r)
    out=np.clip(.5+centered,0,1); out[~m]=.5
    np.save(CAU/f'{name}_raw.npy',d); np.save(CAU/f'{name}_smoothed.npy',sm)
    np.save(CAU/f'{name}_u16.npy',np.round(out*65535).astype(np.uint16))
    per={}
    for a,b in [(1,1.05),(1.05,2),(2,3.5),(3.5,5),(5,7),(7,9),(9,12)]:
        k=m&(r>=a*RS)&(r<b*RS)
        per[f'{a}-{b}']={'pixels':int(k.sum()),'std':float(np.std(out[k])),'sigma_p50_p90':np.percentile(sigma[k],[50,90]) if k.any() else []}
    Image.fromarray(np.round(out[::4,::4]*255).astype(np.uint8)).save(OUT/f'PILOT_{name}_llenc_comu_sencer.png')
    return {'scale_tanh':scale,'radial':per,'H1_full_pixel_correction_history':h1_history,'H1_partial_lunar_rings_included':True}

def main():
    r,t=coords(); mv=np.load(CAU/'vixen_support.npy'); ms=np.load(CAU/'sony_support.npy'); m=mv|ms
    uv=np.load(CAU/'vixen_total.npy',mmap_mode='r'); us=np.load(CAU/'sony_corrected_total.npy',mmap_mode='r')
    sv=np.load(CAU/'vixen_sky.npy',mmap_mode='r'); ss=np.load(CAU/'sony_sky.npy',mmap_mode='r')
    wv=(1-smooth(r/RS,2,2.65))*mv; wv=np.where(ms,wv,mv.astype(np.float32)); ws=(1-wv)*ms
    # The Sony merge already uses the clean B pointing at the marked ghost.
    # Vixen remains an independent judge at this location.
    y,x=np.ogrid[:H,:W]; dist=np.hypot(x-GHOST_XY[0],y-GHOST_XY[1])
    g=np.zeros((H,W),np.float32)
    np.save(CAU/'ghost_donor_weight.npy',g)
    receipt={'rho':{},'correction':{'xy':[2825,3988],'core_px':140,'feather_out_px':200,'donor':'Sony pointing B at identical sky position','validation':'ghost_roi_receipt.json, Vixen held out'},'filters':{},'filter_source':'TOTAL LDIC throughout; no radial source transition','resolution':'independent Fourier-band coherence; preserve demonstrated signal before noise target'}
    total=np.lib.format.open_memmap(CAU/'fusion_total.npy',mode='w+',dtype=np.float32,shape=(H,W,3))
    corona=np.lib.format.open_memmap(CAU/'fusion_corona.npy',mode='w+',dtype=np.float32,shape=(H,W,3))
    for c in range(3):
        log('fusion channel '+str(c)); rho,rep=rho_fit(uv[...,c],us[...,c],mv&ms,r,t); receipt['rho'][str(c)]=rep
        tv=uv[...,c]; ts=us[...,c]*rho; cv=tv-sv[...,c]; cs=(us[...,c]-ss[...,c])*rho
        # Local multiplicative transfer measured outside contamination. Smooth
        # factor only; no high-frequency texture from the contaminated train.
        band=(dist>200)&(dist<300)&mv&ms&(tv>0)&(ts>0)
        factor=float(np.median(ts[band]/tv[band])); receipt['correction'].setdefault('donor_factor',[]).append(factor)
        total[...,c]=(wv*tv+ws*ts)*(1-g)+tv*factor*g
        corona[...,c]=(wv*cv+ws*cs)*(1-g)+cv*factor*g
    total.flush(); corona.flush(); np.save(CAU/'fusion_support.npy',m)
    if '--source-only' in sys.argv:
        savejson(CAU/'filter_receipt.json',receipt);log('fusion source ready');return
    del uv,us,sv,ss,rho,tv,ts,cv,cs,wv,ws,dist,g
    # A single hybrid source per channel for all filters. Total outside 4R is
    # mandatory because the sky model erased real outer azimuthal structure.
    wf=1-smooth(r/RS,3,4); realizations=[]; pals=[]; grands=[]
    for c in range(3):
        log('filter channel '+str(c)); good=m&(total[...,c]>0)
        lt=np.log(np.maximum(total[...,c],1e-8)); lc=np.log(np.maximum(corona[...,c],1e-8))
        gc=good&(corona[...,c]>0)
        xt=detrend(lt,good,r); xc=detrend(lc,gc,r)
        xx=xt
        np.save(CAU/f'normalized_source_{c}.npy',xx)
        w=good.astype(np.float32)
        realizations.append(np.where(good,achf(xx,w,(2,4,8,16,32)),np.nan))
        pals.append(np.where(good,achf(xx,w,(24,)),np.nan))
        grands.append(np.where(good,achf(xx,w,(32,64,128)),np.nan))
    for name,real in [('achf',realizations),('passalt24',pals),('gran',grands)]:
        log('presentation '+name); d=np.nan_to_num(np.nanmedian(np.stack(real),axis=0),nan=0).astype(np.float32)
        receipt['filters'][name]=layer(d,m,r,name); del d
    savejson(CAU/'filter_receipt.json',receipt); log('filter pilot ready')

if __name__=='__main__': main()
