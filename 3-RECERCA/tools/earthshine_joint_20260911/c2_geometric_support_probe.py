"""Counterfactual display-only support diagnostic on the exact V48 composite.
Apply observed geometric support to the aggregate lunar contribution, keeping
the native solar background. This is NOT an approved reconstruction or PSB.
Do not mistake a photographic dark rim for recovered physical lunar texture.
"""
from joint_common import *
from scipy.ndimage import gaussian_filter
from PIL import Image
z=np.load(OUT/'C1_native_composition_roi.npz');base=z['baseline'].astype(float);solar=z['solar_background'].astype(float)
with np.load(OUT/'A2_occlusion_polygon.npz') as a:P=a['P64']
sigma=json.loads((OUT/'A4_profile_operator_probe.json').read_text())['inverse_mapping_estimate'];blur=gaussian_filter(P,sigma,mode='reflect',truncate=8);assert blur.min()>-1e-12 and blur.max()<1+1e-12
images={'V48':base};stats=[];y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY)
for name,a in [('geometric_area',P),('blurred_geometric_area',np.clip(blur,0,1))]:
    trial=np.rint(a[...,None]*base+(1-a[...,None])*solar);assert trial.min()>=0 and trial.max()<=65535
    d=trial-base;stats.append(dict(name=name,max_change_inside_r435_DN16=int(abs(d[r<435]).max()),max_change_DN16=int(abs(d).max()),changed_pixels=int(np.any(d!=0,axis=2).sum())))
    images[name]=trial
np.savez_compressed(OUT/'C2_geometric_support_probe.npz',**{k:v.astype(np.uint16) for k,v in images.items()})
row=np.concatenate([images[k][200:1200,200:1200]/256 for k in images],axis=1).astype(np.uint8);Image.fromarray(row).save(OUT/'vistes/C2_geometric_support_comparison.png')
for name,box in [('top',(540,220,860,290)),('right',(1100,530,1180,860))]:
    x1,y1,x2,y2=box;parts=[images[k][y1:y2,x1:x2]/256 for k in images];row=np.concatenate(parts,axis=1 if name=='right' else 0).astype(np.uint8);im=Image.fromarray(row);im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).save(OUT/f'vistes/C2_{name}_support_x3.png')
save('C2_geometric_support_probe.json',dict(method=__doc__,variants=stats,blur_sigma=sigma,status='Counterfactual diagnostic only; NOT promoted',limits=['The measured optical edge is not independently qualified here as exact physical terrain','Blending the composite in displayRGB is not a physical separation of PSF-scattered light','The central V48 style is numerically retained in this probe; no new texture is supplied','No mask or Photoshop layer changed; these images cannot stand in for a native PSB validation']))
print(stats,flush=True)
