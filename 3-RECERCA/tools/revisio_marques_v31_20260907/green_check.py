"""Descriptive cross-train checks at reviewed green-mark neighborhoods, not arc identification."""
from extract import *
from scipy.ndimage import gaussian_filter
old=ROOT/'research/tools/v29/cau_final'
v=np.load(old/'vixen_total.npy',mmap_mode='r');s=np.load(old/'sony_corrected_total.npy',mmap_mode='r')
mv=np.load(old/'vixen_support.npy',mmap_mode='r');ms=np.load(old/'sony_support.npy',mmap_mode='r')
points=[('M02_NW',4820,3420),('M02_N',5340,3100),('M03_NE',5770,3380),('M04_E',6079,3665),
    ('M05_ESE',6056,3959),('M06_SSW',5160,4260),('M07_SE',5885,4280),('M08_S',5441,4369),('M09_S',5384,4380)]
n=128;guard=96;side=n+2*guard;core=np.s_[guard:guard+n,guard:guard+n]
y,x=np.mgrid[-1:1:complex(n),-1:1:complex(n)];X=np.stack([np.ones_like(x),x,y,x*x,x*y,y*y],axis=-1).reshape(-1,6)
def detr(a):return a.ravel()-X@np.linalg.lstsq(X,a.ravel(),rcond=None)[0]
def corr(a,b):return float(np.corrcoef(a.ravel(),b.ravel())[0,1])
def band(a,m,lo,hi):
    z=np.where(m,np.log(np.maximum(a,1e-20)),0)
    def g(sig):return gaussian_filter(z,sig,truncate=3)/np.maximum(gaussian_filter(m.astype(float),sig,truncate=3),1e-15)
    return (g(lo)-g(hi))[core]
rows=[]
for name,cx,cy in points:
    sl=np.s_[cy-side//2:cy+side//2,cx-side//2:cx+side//2]
    a=np.array(v[sl][...,1],float);b=np.array(s[sl][...,1],float)
    ma=mv[sl]&(a>0);mb=ms[sl]&(b>0);valid=ma[core]&mb[core]
    row={'region':name,'xy':[cx,cy],'valid_core_pixels':int(valid.sum()),'core_pixels':n*n,'bands':[]}
    if valid.all():
        for lo,hi in [(2,8),(8,24)]:
            aa=detr(band(a,ma,lo,hi));bb=detr(band(b,mb,lo,hi))
            row['bands'].append({'diagnostic_gaussian_sigmas':[lo,hi],'cross_train_correlation':corr(aa,bb),
                'same_patch_rotated180_control':corr(aa.reshape(n,n),bb.reshape(n,n)[::-1,::-1])})
        row['status']='local structure corroborated; each marked contour still undetermined'
    else:row['status']='INCOMPLETE_CORE; no filling or result'
    rows.append(row)
write(RUN.rebut('green_cross_train.json'),{'rows':rows,'inputs':[str(old/f) for f in ['vixen_total.npy','sony_corrected_total.npy','vixen_support.npy','sony_support.npy']],
    'method':'Original G; log; support-normalized Cartesian Gaussian differences, truncate3;128px core,96px guard; identical local quadratic detrend',
    'control':'Sony same patch rotated180 after filtering/detrending, not another solar azimuth; descriptive, not calibrated significance',
    'scope':'eight valid neighborhood cores; confirms shared structure not each painted ripple; no claim of physical independence of all processing or of WOW authenticity',
    'verdict':'all eight green brush components remain DUBTOSES'})
print('GREEN CHECK COMPLETE',flush=True)
