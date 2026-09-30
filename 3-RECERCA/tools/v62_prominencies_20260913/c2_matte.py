from pathlib import Path
import sys,json,numpy as np,tifffile as tf,cv2
from scipy.ndimage import label,binary_dilation,distance_transform_edt,gaussian_filter
R=Path.cwd();O=R/'output/v62_prominencies_20260913';A=O/'arrays';P=R/'output/v61_interiors_limbe_20260913'
source=tf.imread(P/'V61_interiors_only.tif').astype('float32')/65535
assert source.shape[:2]==(2000,2000)
rgb=source if source.shape[2]==3 else np.divide(source[...,:3],source[...,3:],out=np.zeros_like(source[...,:3]),where=source[...,3:]>0)
mx=rgb.max(-1);labs,n=label(mx<.05);core=labs==labs[1000,1000];outer=distance_transform_edt(~core);valid=~binary_dilation(core,iterations=5);den=gaussian_filter(valid.astype('float32'),8);bg=gaussian_filter(rgb[...,1]*valid,8)/np.maximum(den,1e-8)
cover=np.maximum(mx,np.clip(rgb[...,1]/np.maximum(bg,1e-8),0,1));cover[outer>10]=1
alpha=np.ceil(np.clip(cover,0,1)*65535).astype('uint16');alpha=np.maximum(alpha,np.rint(mx*65535).astype('uint16'));aa=alpha/65535;fg=np.divide(rgb,aa[...,None],out=np.zeros_like(rgb),where=aa[...,None]>0)
error=abs(fg*aa[...,None]-rgb).max();assert error<1e-7
np.save(A/'C2_matte_alpha16_local.npy',alpha);np.save(A/'C2_original_RGB16_local.npy',np.rint(rgb*65535).astype('uint16'))
rows=[]
for name,bb in [('top',(5250,3303,5305,3350)),('NW',(4970,3460,5050,3550)),('west',(4870,3720,4970,4000)),('SE',(5770,3910,5820,3990))]:
 x0,y0,x1,y1=bb;sl=np.s_[y0-2777:y1-2777,x0-4377:x1-4377];rr=rgb[sl];al=aa[sl];bright=(rr[...,0]>.45)&((rr[...,0]-rr[...,1]>.15)|(rr.min(-1)>.7));rows.append(dict(name=name,protected=int(bright.sum()),max_source_reconstruction_DN16=float(abs((fg*aa[...,None]-rgb)[sl][bright]).max()*65535) if bright.any() else None,protected_with_alpha_one=int((bright&(al==1)).sum())))
(O/'C2_matte_validation.json').write_text(json.dumps(dict(source_native=str(P/'V61_interiors_only.tif'),ROI_global=[4377,2777,6377,4777],ROI_in_object=[3480,2365,5480,4365],parameters=dict(black_component_maxRGB=.05,continuum_sigma=8,exclude_black_dilation=5,outer_transition=10),all_source_premultiplied_max_DN16=float(error*65535),protected_regions=rows,physical_geometry_change=False,claim='Photographic foreground dematting; original source radiance not re-estimated. Zero-black recomposition exact; native verification required.'),indent=2));print('MATTE READY',error,rows,flush=True)
