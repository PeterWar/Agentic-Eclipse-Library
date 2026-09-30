"""Actual Pearson azimuthal alignment, with a genuine 180-degree null."""
from common import *
from inspect_inputs import channel
from psd_tools import PSDImage
from scipy.ndimage import gaussian_filter1d

def polar(a,cx,cy,rs,radii,angle=0,nth=1440):
    th=np.arange(nth,dtype=np.float32)*2*np.pi/nth+angle
    mx=(cx+radii[:,None]*rs*np.cos(th)).astype(np.float32)
    my=(cy+radii[:,None]*rs*np.sin(th)).astype(np.float32)
    return cv2.remap(a.astype(np.float32),mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=np.nan)

def features(p):
    # An azimuthal band retains corona geometry and rejects the invariant
    # radial brightness slope. No normalization by the correlation maximum.
    p=np.asarray(p,np.float32); ok=np.isfinite(p)
    p=np.where(ok,p,0)
    p=gaussian_filter1d(p,1,axis=1,mode='wrap')-gaussian_filter1d(p,28,axis=1,mode='wrap')
    p-=np.mean(p,axis=1,keepdims=True)
    scale=np.sqrt(np.mean(p*p,axis=1,keepdims=True))
    return p/np.maximum(scale,1e-8),ok

def correlate(a,b):
    a,ma=features(a); b,mb=features(b)
    rows=(ma.mean(axis=1)>.98)&(mb.mean(axis=1)>.98)&(np.std(a,axis=1)>.01)&(np.std(b,axis=1)>.01)
    if rows.sum()<4:return {'status':'INDETERMINATE','valid_rings':int(rows.sum())}
    a=a[rows]; b=b[rows]; n=a.shape[1]
    cc=np.fft.irfft(np.fft.rfft(a,axis=1)*np.conj(np.fft.rfft(b,axis=1)),n=n,axis=1).sum(axis=0)
    cc/=np.sqrt(np.sum(a*a)*np.sum(b*b)); k=int(np.argmax(cc)); angle=(k if k<n/2 else k-n)*360/n
    local=np.r_[cc[:9],cc[-8:]]; k0=int(np.argmax(local)); residual=(k0 if k0<9 else k0-17)*360/n
    # significance against rotations separated by at least 5 degrees.
    far=cc.copy(); far[:21]=np.nan; far[-20:]=np.nan
    margin=float(cc[0]-np.nanpercentile(far,99))
    return {'valid_rings':int(rows.sum()),'peak_angle_deg':angle,'peak_pearson':float(cc[k]),'at_zero_pearson':float(cc[0]),'null_180_pearson':float(cc[n//2]),'zero_minus_far_p99':margin,'PASS':bool(abs(angle)<=.5 and cc[0]>.15 and cc[0]-cc[n//2]>.1 and margin>0)}

def main():
    s=PSDImage.open(CAU/'input_V28.psb'); ref=np.load(CAU/'fusion_total.npy',mmap_mode='r')[...,1]
    radii=np.linspace(1.12,2.5,60).astype(np.float32)
    # Test input corruption: full-circle alignment must reject +/-1 degree.
    R=polar(np.log(np.maximum(ref,1)),W/2,H/2,RS,radii)
    control={str(deg):correlate(np.roll(R,round(deg*4),axis=1),R) for deg in (0,1,-1,180)}
    assert control['0']['PASS'] and not control['1']['PASS'] and not control['-1']['PASS'] and not control['180']['PASS']
    rep={'coordinates':{'common_sun':[W/2,H/2],'final_sun':[CX,CY],'M':M},'known_bad_controls':control,'layers':[]}
    noncoronal={0:'C2 protected pearls',1:'C2 protected lunar limb',14:'lunar earthshine',15:'external comparison image',16:'lunar LROC comparison',17:'lunar earthshine V24e',24:'stellar coordinates',25:'local lens-reflection correction'}
    for i,l in enumerate(s):
        if i in noncoronal:
            rep['layers'].append({'i':i,'name':l.name,'coordinate_frame':noncoronal[i],'solar_alignment':'N/A; preserve source registration and verify channel/mask identity'});continue
        a=channel(l,1).astype(np.float32)/65535
        radii=np.linspace(*( (3,5.5) if i==12 else (5,8) if i==13 else (1.12,1.5) if i==2 else (1.2,2.3)),60).astype(np.float32)
        P=polar(a,CX-l.left,CY-l.top,RS,radii)
        R=polar(np.log(np.maximum(ref,1)),W/2,H/2,RS,radii,angle=-np.arctan2(M[1,0],M[0,0]))
        result=correlate(P,R)
        item={'i':i,'name':l.name,'radius_range':[float(radii.min()),float(radii.max())],**result};rep['layers'].append(item);log(str(item));del a
    savejson(CAU/'input_geometry_audit.json',rep)

if __name__=='__main__':main()
