"""Smooth empirical differential response of saved photo to source detector.
The constant coefficient in D0/D6 extrapolated an interior fit into a region
where the source-to-display mixture differs. D8 diagnosed this using only even
sectors. Fit six nonnegative Bernstein coefficients for beta(r) and gamma(r)
on angular16-64, r60-435 even sectors. Degree2 in u=(r/DOMAIN)^2. Full last limb
remains outside fit. No external pixels or mark-specific mask; no endpoint
value fixed. Apply the smooth gamma to the repeatable detector correction only.
"""
from common import *
from spectral import *
from scipy.optimize import nnls
from PIL import Image
claim();rr0,_=geometry();aa0=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/V53_lunar_alpha.npy');mm0=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/V53_lunar_mask.npy');DOMAIN=float(rr0[(aa0>0)&(mm0>0)].max());save('D10_protocol.json',dict(method=__doc__,domain=DOMAIN,domain_reason='D9 used450 smaller than existing visible support457.6, violating positivity of Bernstein outside its domain. This corrected variant uses the exact maximum radius of existing alpha/mask support, no mask change; no D9 product.',basis='[(1-u)^2,2u(1-u),u^2], u=(r/DOMAIN)^2; globally smooth polynomial, fitted endpoints, not a radial taper/mask',fit='even sectors60-435, fixed16-64; 6 coefficients>=0 by NNLS; no Sony/LROC/green marks',gates='Exact inherited92 claims, source external, fixed differential injection, no clipping or new halo, native Photoshop before PSB',limits=['A new transport model motivated by D8, not independent confirmation of D0/D6','Saved CameraRaw not replayed; empirical response only','Repeated external evaluation is exploratory; no formal significance or novel-feature claim']))
z=np.load(OUT/'arrays/B11_repeatable_all.npz');S,V=polar(z['source']);D,_=polar(z['correction']);old=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/D1_candidate_rgb.npy').astype(np.int32);P,_=polar(old.mean(-1));A,B,Q=[angular_band(v,16,64) for v in [S,D,P]];u=(RR[:,None]/DOMAIN)**2;basis=np.broadcast_to(np.stack([(1-u)**2,2*u*(1-u),u*u],-1),(*A.shape,3));tr=sector_mask(60,435,0)&V;ho=sector_mask(60,435,1)&V
X=np.concatenate([A[...,None]*basis,B[...,None]*basis],-1);cf,res=nnls(X[tr],Q[tr]);beta=(basis*cf[:3]).sum(-1);gamma=(basis*cf[3:]).sum(-1);pred=beta*A+gamma*B
r,t=geometry();v=(r/DOMAIN)**2;basis2=np.stack([(1-v)**2,2*v*(1-v),v*v],-1);g=(basis2*cf[3:]).sum(-1);mask=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/V53_lunar_mask.npy');alpha=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/V53_lunar_alpha.npy');hidden=(mask==0)|(alpha==0);delta=-np.rint(g*z['correction']).astype(np.int32);delta[hidden]=0;new=old+delta[...,None]
save('D10_response.json',dict(coefficients=cf,heldout_r=corr(pred,Q,ho),heldout_residual_rms=float(np.std((Q-pred)[ho])),gamma_by_radius=[dict(radius=rr,gamma=float(np.array([(1-(rr/DOMAIN)**2)**2,2*(rr/DOMAIN)**2*(1-(rr/DOMAIN)**2),(rr/DOMAIN)**4])@cf[3:])) for rr in [60,250,350,410,435,449]],minmax=[int(new.min()),int(new.max())],hidden_exact=bool(np.array_equal(new[hidden],old[hidden])),source_sha256=sha(OUT/'arrays/B11_repeatable_all.npz')))
assert new.min()>=0 and new.max()<=65535,'Clipping: reject';assert np.all(g[~hidden]>=0),'Negative response: reject';np.save(OUT/'arrays/D10_candidate_rgb.npy',new.astype(np.uint16));np.save(OUT/'arrays/D10_delta.npy',delta);np.save(OUT/'arrays/D10_gamma.npy',g)
print('SPATIAL RESPONSE',cf,'heldout r',corr(pred,Q,ho),flush=True)
