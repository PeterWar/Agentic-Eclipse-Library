"""Transport measured detector contamination to the saved V54 appearance.
Fit Photo = beta*clean_source + gamma*detector_component in training Fourier
bands. Only gamma*detector is subtracted; saved CameraRaw residual is fixed.
This does not substitute a source image or identify CameraRaw controls.
"""
from common import *
from spectral import *
from PIL import Image
claim();z=np.load(OUT/'arrays/B3_G67_robust_hetero_full_safe_all.npz');S,V=polar(z['source']);D,_=polar(z['correction']);old=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/D1_candidate_rgb.npy').astype(np.int32);P,_=polar(old.mean(-1))
mask=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/V53_lunar_mask.npy');alpha=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/V53_lunar_alpha.npy')
train=sector_mask(60,350,0)&V;test=sector_mask(60,350,1)&V
save('D0_protocol.json',dict(method=__doc__,model='Two scalar coefficients through zero across fixed16-64px angular Fourier band: saved V54 luminance vs cleaned G source and detector contamination. Primary: subtract fitted gamma times actual two-dimensional detector correction, without a new band/filter/mask.',fit='A0 even sectors, r60-350 only; Sony/LROC excluded. Holdout odd sectors. Per-band slopes and leave-sector-out diagnostics report identification, not select gamma.',gates=['Source improvement and injection test for exact source branch','Photographic retention Sony/LROC and rotated null, all previous retained claims','Saved geometry/alpha/masks/chroma and25other layers exact','No new halo/seam: inherited V54 limb compared with same profiles and whole-canvas1:1','Paired differential injection through source and fixed display transport','Photoshop native readback/dos lectors before new PSB'],limits=['Empirical differential photometric model, not a native CameraRaw reconstruction','Photographic Sony comparison is retention because old broad base already includes Sony','If coefficient is unphysical or heldout/visual gates fail, no product']))
A=angular_band(S,16,64);B=angular_band(D,16,64);Q=angular_band(P,16,64);X=np.stack([A[train],B[train]],1);coef=np.linalg.lstsq(X,Q[train],rcond=None)[0];beta,gamma=coef
pred=beta*A+gamma*B;bandrows=[]
for band in [[16,24],[24,40],[40,64],[64,96]]:
    a=angular_band(S,*band);b=angular_band(D,*band);q=angular_band(P,*band);xx=np.stack([a[train],b[train]],1);cf=np.linalg.lstsq(xx,q[train],rcond=None)[0]
    bandrows.append(dict(band=band,beta=float(cf[0]),gamma=float(cf[1]),condition=float(np.linalg.cond(xx)),heldout_residual_rms=float(np.std(q[test]-cf[0]*a[test]-cf[1]*b[test]))))
loo=[]
for sec in [0,2,4,6,8,10]:
    tr=train&((np.arange(NT)[None,:]//120)!=sec);xx=np.stack([A[tr],B[tr]],1);cf=np.linalg.lstsq(xx,Q[tr],rcond=None)[0];loo.append(dict(omitted_sector=sec,beta=float(cf[0]),gamma=float(cf[1])))
rep=dict(beta=float(beta),gamma=float(gamma),condition=float(np.linalg.cond(X)),heldout_r=corr(pred,Q,test),heldout_residual_rms=float(np.std(Q[test]-pred[test])),per_band=bandrows,leave_sector_out=loo,source_sha256=sha(OUT/'arrays/B3_G67_robust_hetero_full_safe_all.npz'),photo_sha256=sha(ROOT/'output/earthshine_v54_detail_20260913/arrays/D1_candidate_rgb.npy'))
save('D0_frozen_response.json',rep);print('PHOTO MODEL',rep,flush=True)
assert 0<beta and 0<gamma<4*beta,'Unidentified/nonphysical response; no candidate'
delta=-np.rint(gamma*z['correction']).astype(np.int32);hidden=(mask==0)|(alpha==0);delta[hidden]=0;new=old+delta[...,None]
assert new.min()>=0 and new.max()<=65535,'Candidate would clip; reject'
np.save(OUT/'arrays/D0_candidate_rgb.npy',new.astype(np.uint16));np.save(OUT/'arrays/D0_delta.npy',delta)
save('D0_candidate.json',dict(delta_minmax=[int(delta.min()),int(delta.max())],delta_p95=float(np.percentile(abs(delta)[~hidden],95)),hidden_exact=bool(np.array_equal(new[hidden],old[hidden])),chroma_exact=bool(np.array_equal(new[...,0]-new[...,1],old[...,0]-old[...,1]) and np.array_equal(new[...,2]-new[...,1],old[...,2]-old[...,1])),status='PILOT ONLY, gates pending'))
def preview(a):return np.clip(np.rint(a/257.),0,255).astype('uint8')
Image.fromarray(preview(old)).save(OUT/'vistes/D0_V54_moon_1a1.png');Image.fromarray(preview(new)).save(OUT/'vistes/D0_candidate_moon_1a1.png')
panel=np.concatenate([preview(old),preview(new)],1);Image.fromarray(panel).save(OUT/'vistes/D0_comparison_1a1.png')
