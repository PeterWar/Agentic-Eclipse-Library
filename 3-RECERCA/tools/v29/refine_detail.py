"""NRGF contrast normalization followed by local multiscale detail.

The previous pilot subtracted the radial profile but omitted the NRGF
contrast division. Its global display scale then overemphasized the inner
corona. This keeps the observed azimuthal contrast on a common scale, with
a floor at 3.5R that prevents boosting noise-dominated outer annuli.
"""
from common import *
from fuse_and_filter import achf,layer
from scipy.ndimage import gaussian_filter1d

def contrast_profile(x,m,r):
    sm=normgauss(x,m.astype(np.float32),8)
    cen,p=radial_profile(np.abs(sm),m,r,nb=120,stride=3)
    p=np.maximum(1.4826*p,.002)
    floor=float(np.interp(np.log(3.5),cen,p));p=np.where(cen>np.log(3.5),np.maximum(p,floor),p)
    p=gaussian_filter1d(p,2)
    scale=np.interp(np.log(np.maximum(r/RS,1e-5)),cen,p).astype(np.float32)
    return scale,{'lnr_centres':cen,'robust_contrast':p,'outer_floor_at_3_5R':floor,'statistic':'MAD of 8px-smoothed radial-centered ln TOTAL; interpolated profile'}

def main():
    r,_=coords();m=np.load(CAU/'fusion_support.npy');total=np.load(CAU/'fusion_total.npy',mmap_mode='r');reals={n:[] for n in ('achf','passalt24','gran')};rep={'profiles':{},'filters':{},'NRGF':'filter ln TOTAL directly; radial contrast division AFTER filtering; H1 after tanh/SN; no radial median subtraction before filtering and no circular support cut','gran_definition':'mean of G8-G32, G8-G64, G8-G128; isotropic normalized convolutions, no polar sampling'}
    for c in range(3):
        good=m&(total[...,c]>0);x=np.log(np.maximum(total[...,c],1e-8));centered=detrend(x,good,r);scale,p=contrast_profile(centered,good,r);rep['profiles'][str(c)]=p
        np.save(CAU/f'nrgf_source_{c}.npy',x/scale)
        w=good.astype(np.float32)
        reals['achf'].append(np.where(good,achf(x,w,(2,4,8,16,32))/scale,np.nan))
        reals['passalt24'].append(np.where(good,achf(x,w,(24,))/scale,np.nan))
        reals['gran'].append(np.where(good,(normgauss(x,w,8)-(normgauss(x,w,32)+normgauss(x,w,64)+normgauss(x,w,128))/3)/scale,np.nan))
        log('NRGF full contrast channel '+str(c))
    for name,rr in reals.items():
        d=np.nan_to_num(np.nanmedian(np.stack(rr),axis=0),nan=0).astype(np.float32);rep['filters'][name]=layer(d,m,r,name);log('refined '+name)
    savejson(CAU/'refined_detail_receipt.json',rep);log('detail refined')

if __name__=='__main__':main()
