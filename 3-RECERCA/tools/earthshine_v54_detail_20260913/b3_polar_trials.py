"""Boundary-qualified source bands; tiny pre-CameraRaw promotion, no new texture.
Radial component is unchanged. Source confidence never supplies external pixels.
"""
from common import *
from scipy.ndimage import map_coordinates,gaussian_filter
from scipy.fft import dctn,idctn
claim();r,theta,d=geometry();nt=2880;rr=np.arange(0.,456.,.5);th=np.arange(nt)*2*np.pi/nt
co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)]
freq=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*np.maximum(rr[:,None],.25))
def pol(a):return map_coordinates(a,co,order=3,mode='nearest')
def cart(p):
    # Wrap angular coordinate only. Radius interpolated on its native range.
    pad=np.concatenate([p[:,-2:],p,p[:,:2]],1)
    return map_coordinates(pad,[np.minimum(r/.5,len(rr)-1),theta*nt/(2*np.pi)+2],order=3,mode='nearest')
def band(p,lo=40,hi=64):
    # Smooth Fourier skirt at 32-40 and 64-80 avoids Gibbs ringing.
    u=np.clip((freq-1/80)/(1/64-1/80),0,1);v=np.clip((freq-1/40)/(1/32-1/40),0,1)
    H=(.5-.5*np.cos(np.pi*u))*(.5+.5*np.cos(np.pi*v))
    return np.fft.irfft(np.fft.rfft(p,axis=1)*H,n=nt,axis=1)
z=np.load(OUT/'arrays/B1_stacks.npz');B={k:band(pol(z[k])) for k in ['all','half0','half1','early','late']}
noise=gaussian_filter((.5*(B['half0']-B['half1']))**2,(32,nt/36),mode=('nearest','wrap'))
power=gaussian_filter(B['all']**2,(32,nt/36),mode=('nearest','wrap'))
wi=np.clip(1-noise/np.maximum(power,1e-30),0,1);ga=np.clip(1-9*noise/np.maximum(B['all']**2,1e-30),0,1)
gain=np.maximum(wi,ga)
# Confidence uses all band power; temporal discrepancy is separate conservative
# limitation, not subtracted as noise because the PSF also changes in time.
rows=[]
for lo,hi in [(100,300),(300,370),(370,435),(435,449)]:
    m=(rr>=lo)&(rr<hi);rows.append(dict(radius=[lo,hi],rms=float(np.std(B['all'][m])),noise=float(np.std(.5*(B['half0']-B['half1'])[m])),temporal=float(np.std(.5*(B['early']-B['late'])[m])),gain_median=float(np.median(gain[m]))))
np.save(OUT/'arrays/B3_confidence_polar.npy',gain.astype('float32'))
np.save(OUT/'arrays/B3_source_denoised.npy',z['all']+cart((gain-1)*B['all']))
# Production pilot promotes ALREADY corroborated original pre-CR detail; no
# independent recovery claim, and no Vixen substitution for the better photo.
pre=np.load(SRC/'full_sampler_delta/C0_pre_camera_raw_rgb.npy');p=pol(pre.mean(-1));b=band(p)
# Physical lunar mask inherited from V53. Added signal goes to zero where that
# input has no lunar support. No new radius/crop or photographic alpha.
mask=np.load(OUT/'arrays/V53_lunar_mask.npy')/65535.;pm=pol(mask)
delta=.08*gain*b*np.clip(pm,0,1)
dc=cart(delta);dc[mask==0]=0
new=np.clip(np.rint(pre.astype(float)+dc[...,None]),0,65535).astype('uint16')
np.save(OUT/'arrays/B3_preCR_candidate.npy',new)
np.save(OUT/'arrays/B3_preCR_delta.npy',new.astype('int32')-pre.astype('int32'))
# Blind deterministic injections are generated only after the operator/gains
# above have been fixed; test intrinsic transfer with the frozen confidence.
rng=np.random.default_rng(540913);inj=[]
for j in range(8):
    a=band(rng.normal(size=p.shape));a*=np.sin(np.pi*np.minimum(rr,456)/456)[:,None]**2
    o=a+.08*gain*band(a)*np.clip(pm,0,1)
    for lo,hi in [(100,300),(300,370),(370,435),(435,449)]:
        m=(rr>=lo)&(rr<hi);v=a[m];q=o[m];t=float(np.sum(v*q)/np.sum(v*v));inj.append(dict(seed_index=j,radius=[lo,hi],transfer=t,pass_gate=.9<=t<=1.1))
save('B3_source_bands.json',dict(rows=rows,production_pilot='8 percent maximum tangential 40-64px promotion of original pre-CameraRaw photographic source, confidence from balanced Vixen halves; max(Wiener,garrote3). No new recovery/resolution claim.',
    rejected_B1='Cartesian full-square DCT contained bright exterior corona: source bands polluted, Sony judge collapsed; not used.',
    limitations=['Tangential detail only; radial structure retained verbatim at this stage.','Confidence can contain fixed-pattern noise; source and photographic judges must pass.','No improvement in the final 14px is claimed.'],injection=inj,
    preCR_delta_DN16=dict(p50=float(np.percentile(abs(dc)[mask>.5],50)),p95=float(np.percentile(abs(dc)[mask>.5],95)),max=float(abs(dc).max()))))
print('B3',rows,'injection',min(a['transfer'] for a in inj),max(a['transfer'] for a in inj),flush=True)
