"""Explicitly requested PHOTOGRAPHIC edge grading of the live V45 source.

The profile is a display-luminance reference, never a physical PSF estimate.
No spatial filtering of image pixels; only a positive smooth multiplicative
field. The original lunar mask and the contribution of layer09 are retained.
"""
from comu46 import *
from a1_grade import field
from scipy.stats import binned_statistic
from scipy.ndimage import gaussian_filter1d

def smoothstep(t):
    t=np.clip(t,0,1);return t**3*(10+t*(-15+6*t))

def main():
    claim46()
    old=np.load(CAU46/'live_lunar_rgb_u16.npy').astype(float)/65535
    w=np.load(CAU46/'live_lunar_mask_u16.npy').astype(float)/65535
    base=np.load(CAU46/'live09_roi_u16.npy').astype(float)/65535
    live=np.load(CAU46/'before_live_rgb_u16.npy')
    assert np.max(np.ptp(old,axis=2))*65535<=2.01 # Photoshop 16-bit roundoff
    before=base*(1-w[...,None])+old*w[...,None]
    dif=abs(np.rint(before*65535).astype(int)-live.astype(int))
    assert dif.max()<=6,('Snapshot recomposition',dif.max())
    _,d=field(1,1)
    edges=np.arange(-25,121,.25);pos=(edges[:-1]+edges[1:])/2
    valid=(d>=edges[0])&(d<edges[-1])
    med=binned_statistic(d[valid],old[...,1][valid],statistic='median',bins=edges)[0]
    assert np.isfinite(med).all()
    profile=gaussian_filter1d(med,2,mode='nearest') # sigma0.5 pixel on 1-D reference only
    print('PROFILE',[(i,float(np.interp(i,pos,profile))) for i in [-5,0,2,5,10,15,20,30,40,50,60,80,100]],flush=True)
    rows=[]
    for key,edge_tone,transition,reach in [('h',.18,8.,100.),('i',.16,12.,110.),('j',.21,8.,70.)]:
        # The neutral tone comes from the interior at the beginning of the grade.
        anchor=float(np.interp(reach,pos,profile))
        desired=edge_tone+(anchor-edge_tone)*smoothstep(pos/transition)
        flat_gain=np.clip(desired/profile,0,1)
        blend=smoothstep((reach-pos)/(reach-transition))
        gp=1-blend*(1-flat_gain)
        gain=np.interp(d,pos,gp,left=gp[0],right=1)
        gain[d>=reach]=1
        # Subtract the same gray amount from all channels to retain the tiny
        # live RGB differences as well as the colored solar contribution.
        subtraction=np.rint(old[...,1]*(1-gain)*65535).astype(np.int32)
        new=(np.rint(old*65535).astype(np.int32)-subtraction[...,None])
        assert new.min()>=0
        new=new.astype(np.uint16)
        after=base*(1-w[...,None])+new.astype(float)/65535*w[...,None]
        np.save(CAU46/f'{key}_gain.npy',gain.astype(np.float32))
        np.save(CAU46/f'{key}_display_u16.npy',new)
        png46(f'A2_{key}_lluna_1a1.png',after)
        for name,(x,y),half in [('dalt',(596,247),60),('dreta',(1088,912),70),('oest',(247,700),75),('baix',(700,1151),70)]:
            sl=np.s_[y-half:y+half,x-half:x+half]
            png46(f'A2_{key}_{name}_x3.png',cv2.resize(np.concatenate([before[sl],after[sl]],1),None,fx=3,fy=3,interpolation=cv2.INTER_NEAREST))
        rows.append(dict(key=key,edge_tone=edge_tone,transition_px=transition,reach_px=reach,anchor=anchor,gain_at_depth=[(i,float(np.interp(i,pos,gp))) for i in [0,5,10,20,40,60,80]],source_inner_exact=bool(np.array_equal(new[d>=reach],np.rint(old[d>=reach]*65535).astype(np.uint16)))))
    savejson(REB46/'A2_variants.json',dict(live_snapshot_recomposition_max_DN16=int(dif.max()),variants=rows,profile_depth=pos.tolist(),profile_luminance=profile.tolist(),scope='User-authorized photographic tone field; no PSF claim or new recovered detail. No image pixel blur or resampling.'))
    print(rows,flush=True)

if __name__=='__main__':main()
