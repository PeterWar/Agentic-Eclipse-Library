import rawpy, numpy as np
from scipy import ndimage as ndi

DIR='/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/'
PED=511.5
H,W=4638,6958
SAT=15800.0

DARK={ '10':'dark_med_10.npy','2':'dark_med_2.npy','1':'dark_med_1.npy' }

def load_raw(f):
    r=rawpy.imread(DIR+f+'.CR3'); im=r.raw_image_visible[:H,:W].astype(np.float32); r.close()
    return im

def hotmask(darkfile, nsig=6.0):
    d=np.load(darkfile)[:H,:W]
    med=np.median(d); mad=np.median(np.abs(d-med))*1.4826
    return (d>med+nsig*max(mad,1.0)) | (d<med-nsig*max(mad,1.0))

def green_full(im, badmask):
    """Interpolate the green quincunx to full res. No channel mixing."""
    g=np.full((H,W),np.nan,dtype=np.float32)
    g[0::2,1::2]=im[0::2,1::2]
    g[1::2,0::2]=im[1::2,0::2]
    if badmask is not None:
        g[badmask]=np.nan
    # fill non-green (and bad green) by mean of valid orthogonal neighbours
    v=np.isfinite(g)
    gv=np.where(v,g,0.0).astype(np.float32); vv=v.astype(np.float32)
    s=np.zeros_like(gv); n=np.zeros_like(vv)
    s[1:,:]+=gv[:-1,:]; n[1:,:]+=vv[:-1,:]
    s[:-1,:]+=gv[1:,:]; n[:-1,:]+=vv[1:,:]
    s[:,1:]+=gv[:,:-1]; n[:,1:]+=vv[:,:-1]
    s[:,:-1]+=gv[:,1:]; n[:,:-1]+=vv[:,1:]
    filled=np.where(n>0,s/np.maximum(n,1),np.nan)
    out=np.where(v,g,filled)
    return out.astype(np.float32)

def plane(im,which):
    if which=='R': return im[0::2,0::2]
    if which=='G1': return im[0::2,1::2]
    if which=='G2': return im[1::2,0::2]
    if which=='B': return im[1::2,1::2]

def block_stat(a, bs, func):
    h=(a.shape[0]//bs)*bs; w=(a.shape[1]//bs)*bs
    b=a[:h,:w].reshape(h//bs,bs,w//bs,bs).transpose(0,2,1,3).reshape(h//bs,w//bs,bs*bs)
    return func(b,axis=2)

def bg_and_sigma(img, bs=24, mask=None):
    """img: full-res float32 with NaN where invalid. Returns background and sigma maps."""
    a=img.copy()
    if mask is not None: a[mask]=np.nan
    coarse=block_stat(a,bs,np.nanmedian)
    coarse=np.where(np.isfinite(coarse),coarse,np.nan)
    # fill NaNs in coarse by nearest finite
    bad=~np.isfinite(coarse)
    if bad.any():
        idx=ndi.distance_transform_edt(bad,return_distances=False,return_indices=True)
        coarse=coarse[tuple(idx)]
    coarse_s=ndi.median_filter(coarse,size=3,mode='nearest')
    zy=img.shape[0]/coarse_s.shape[0]; zx=img.shape[1]/coarse_s.shape[1]
    bgf=ndi.zoom(coarse_s,(zy,zx),order=3)[:img.shape[0],:img.shape[1]]
    res=img-bgf
    r2=res.copy()
    if mask is not None: r2[mask]=np.nan
    csig=block_stat(np.abs(r2),bs,np.nanmedian)*1.4826
    bad=~np.isfinite(csig)|(csig<=0)
    if bad.any():
        idx=ndi.distance_transform_edt(bad,return_distances=False,return_indices=True)
        csig=csig[tuple(idx)]
    csig=ndi.median_filter(csig,size=3,mode='nearest')
    sig=ndi.zoom(csig,(zy,zx),order=1)[:img.shape[0],:img.shape[1]]
    return bgf.astype(np.float32), np.maximum(sig,1e-3).astype(np.float32), res.astype(np.float32)
