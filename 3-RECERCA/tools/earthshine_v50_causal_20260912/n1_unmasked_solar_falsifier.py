"""Causal falsifier requested by independent source audit, not a V50 candidate.
Same K0 geometric alpha and exact Pere lunar RGB; replace only substrate by
observed original layer10 RGB without its historical user mask. No translation,
tone or smoothing. Retain current09-minus-L6 prominence residual separately.
"""
from common50 import *
from PIL import Image
moon=np.load(V49/'A0_Pere_moon_RGB16.npy').astype(float);mask=np.load(OUT/'K0_geometric_mask_u16.npy').astype(float)/65535;current=np.load(OUT/'L0_09_RGB16.npy').astype(float);reco=np.load(OUT/'L6_reconstructed09.npy').astype(float);orig=dict(np.load(OUT/'L4_original_10.npz'));alpha=orig['alpha'].astype(float)/65535
substrate=orig['rgb']*alpha[...,None]+current*(1-alpha[...,None]);res=current-reco
plain=moon*mask[...,None]+substrate*(1-mask[...,None]);retained=plain+res*(1-mask[...,None]);np.save(OUT/'N1_plain_RGB16.npy',np.rint(np.clip(plain,0,65535)).astype(np.uint16));np.save(OUT/'N1_residual_retained_RGB16.npy',np.rint(np.clip(retained,0,65535)).astype(np.uint16))
arrays=[np.load(V49/'A2_Pere_actual_RGB16.npy'),np.load(OUT/'K0_composite_RGB16.npy'),plain,retained];ims=[Image.fromarray((np.clip(z,0,65535).astype(np.uint16)>>8).astype('uint8')) for z in arrays]
for name,box in {'right':(1040,430,1220,940),'left':(165,420,365,960),'top':(370,170,990,365),'bottom':(400,1030,970,1230),'full':(0,0,N,N)}.items():
 crops=[im.crop(box) for im in ims];out=Image.new('RGB',(crops[0].width*4,crops[0].height))
 for i,im in enumerate(crops):out.paste(im,(i*im.width,0))
 out.save(OUT/f'N1_{name}.png')
save('N1_unmasked_solar_falsifier.json',dict(method=__doc__,Moon_RGB_exact=True,K0_alpha_exact=True,source10_user_mask_applied=False,source10_alpha_range=[int(orig['alpha'].min()),int(orig['alpha'].max())],clipping_in_residual_variant=int(np.sum((retained<0)|(retained>65535))),status='visual causal diagnostic, no PSB'))
print('DONE',flush=True)
