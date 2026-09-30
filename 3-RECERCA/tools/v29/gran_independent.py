"""Wide detail filtered per train before blending, without photometric rho.

Filtering ln radiance commutes with a constant exposure gain. A fitted
spatial/radial gain must not be filtered into a coronal structure. G is used
for this broad monochrome derivative because it has the strongest independent
evidence; fine ACHF retains its separately declared RGB-median construction.
"""
from common import *
from refine_detail import contrast_profile
from fuse_and_filter import centre_rings,layer

def main():
    r,_=coords();mv=np.load(CAU/'vixen_support.npy');ms=np.load(CAU/'sony_support.npy');m=mv|ms
    wv=(1-smooth(r/RS,2,2.65))*mv;wv=np.where(ms,wv,mv.astype(np.float32));ws=(1-wv)*ms
    d=np.zeros((H,W),np.float32);contrast=np.zeros((H,W),np.float32)
    for tag,source,mask,weight in [('vixen','vixen_total',mv,wv),('sony','sony_corrected_total',ms,ws)]:
        a=np.load(CAU/f'{source}.npy',mmap_mode='r')[...,1];good=mask&(a>0);x=np.log(np.maximum(a,1e-8));w=good.astype(np.float32)
        band=normgauss(x,w,8)-(normgauss(x,w,32)+normgauss(x,w,64)+normgauss(x,w,128))/3
        sc,profile=contrast_profile(detrend(x,good,r),good,r)
        d+=weight*band;contrast+=weight*sc
        log('wide independent '+tag)
    # Centre the raw derivative before compression, so the partial lunar
    # boundary cannot saturate every azimuth to the same tanh endpoint.
    scale=float(np.percentile(np.abs(d[m]),99));centred,h=centre_rings(d/max(scale,1e-8),m,r);d=centred*scale/np.maximum(contrast,.002)
    rep=layer(d,m,r,'gran');rep.update({'source':'G only; each train filtered separately before blend; no rho in detail','operator':'G8-(G32+G64+G128)/3 on ln TOTAL; raw radial centering before contrast/tanh; final H1 after smoothing','raw_centering_history':h,'raw_scale':scale})
    savejson(CAU/'gran_independent_receipt.json',rep);log('independent wide ready')

if __name__=='__main__':main()
