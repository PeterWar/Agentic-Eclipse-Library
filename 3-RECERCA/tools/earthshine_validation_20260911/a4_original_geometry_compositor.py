"""Transform-domain variant; coarse asinh radiometry exact, not coarse linear radiance. C4 rejected for negative ringing."""
"""Mixed-domain source HDR: radiance at coarse scales, gradients only at fine scales.

Deterministic Cartesian cosine basis on the FULL source rectangle. No circles,
marked-region masks, spatial gain painting or texture from the external judge.
Rejected C3 alters coarse angular evidence; this alternative preserves Cartesian
wavelengths >=16 pixels exactly (nominal), with a smooth8–16px transition.
It still requires independent evidence and boundary/RAW transfer validation.
"""
from validation_common import *
from scipy.ndimage import gaussian_filter1d
from scipy.fft import dctn,idctn
def metrics(im):
    core=im[25:52,35:195];df=np.diff(np.log(np.maximum(core,1e-9)),axis=0);j=np.argmin(df,axis=0)
    aa=df[np.maximum(j-1,0),np.arange(160)];bb=df[j,np.arange(160)];cc=df[np.minimum(j+1,len(df)-1),np.arange(160)]
    sub=np.clip(.5*(aa-cc)/np.maximum(aa-2*bb+cc,1e-30),-.5,.5);pos=j+sub
    return dict(max_fractional_drop_median=float(np.median(1-np.exp(bb))),edge_position_highpass_rms=float(np.std(pos-gaussian_filter1d(pos,5))),negative_count=int((im<=0).sum()))


z=np.load(OUT/'A3_vixen67_original_geometry.npz');base=z['base'];grad=z['asinh8'];delta=np.arcsinh(grad/20.)-np.arcsinh(base/20.)
h,wi=base.shape;freq=np.hypot((np.arange(h)/(2*h))[:,None],(np.arange(wi)/(2*wi))[None,:])
arr=dict(base=base);rep={}
for low,high in [(8,16),(4,8)]:
    t=np.clip((freq-1/high)/(1/low-1/high),0,1);H=.5-.5*np.cos(np.pi*t)
    correction=idctn(dctn(delta,type=2,norm='ortho')*H,type=2,norm='ortho');out=20.*np.sinh(np.arcsinh(base/20.)+correction);key=f'band{low}_{high}';arr[key]=out
    preserved=dctn(np.arcsinh(out/20.)-np.arcsinh(base/20.),type=2,norm='ortho')[freq<=1/high]
    rep[key]=dict(negative=int((out<=0).sum()),preserved_low_frequency_max=float(abs(preserved).max()),top=metrics(out[215:300,585:815]),correction_range=[float(correction.min()),float(correction.max())])
np.savez_compressed(OUT/'A4_original_geometry_compositor.npz',**arr)
(OUT/'A4_original_geometry_compositor.json').write_text(json.dumps(dict(method=__doc__,nominal='band8_16',sensitivity='band4_8',results=rep,status='EXPLORATORY SOURCE COMPOSITOR; not a delivered correction'),indent=2));print(json.dumps(rep),flush=True)
