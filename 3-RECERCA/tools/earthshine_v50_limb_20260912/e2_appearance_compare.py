"""Diagnostic global response match to actual saved V49 pixels.
No inference of the user's unknown baked Camera Raw recipe. Fit a monotone
luminance response on even sectors, assess odd sectors; preserve saved chroma
and optionally saved residual appearance exactly with a response difference.
No photographic probe is qualified by this display comparison.
"""
from common50 import *
import sys
from scipy.optimize import isotonic_regression
from scipy.interpolate import PchipInterpolator
from PIL import Image,ImageDraw
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from c5_fonts_psb import C,PSDImage
s=PSDImage.open(ROOT/'output/earthshine_native_psf_20260911/full_sampler_delta/C1_camera_raw.psd');l=next(l for l in s if l.name=='V45 font G · dos trens · preferència temporal · vel present');old=np.stack([C.channel(l,c) for c in range(3)],-1).mean(-1)
pere=np.load(V49/'A0_Pere_moon_RGB16.npy').astype(float);target=pere.mean(-1);mask=np.load(V49/'A0_inherited_mask_roi.npy').astype(float)/65535;bg=np.load(V49/'A2_sense_font_lunar_RGB16.npy').astype(float);current=np.load(V49/'A2_Pere_actual_RGB16.npy')
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);sec=(np.arctan2(y-CY,x-CX)%(2*np.pi)*24/(2*np.pi)).astype(int);valid=(mask>.8)&(r<458);train=valid&(sec%2==0);test=valid&(sec%2==1)
knots=[]
for lo in np.arange(0,65535,300):
 w=train&(old>=lo)&(old<lo+300)
 if w.sum()>=100:knots.append([float(np.mean(old[w])),float(np.median(target[w])),int(w.sum())])
a=np.array(knots);fity=isotonic_regression(a[:,1],weights=a[:,2]).x;xx=np.r_[0,a[:,0],65535];yy=np.r_[0,fity,65535];f=PchipInterpolator(xx,yy);base=f(old);err=base-target;rep=dict(method=__doc__,knots=knots,isotonic_output=fity.tolist(),heldout_error_DN16=np.percentile(abs(err[test]),[50,95,99,100]).tolist(),train_error_DN16=np.percentile(abs(err[train]),[50,95,99,100]).tolist(),probes={})
for tag in ['physical','pupil']:
 src=np.load(OUT/f'E1_{tag}_RGB16.npy').mean(-1);pred=f(src)
 for method in ['delta','direct']:
  lum=target+pred-base if method=='delta' else pred;rgb=pere+(lum-target)[...,None];clipped=int(((rgb<0)|(rgb>65535)).any(-1).sum());rgb=np.rint(np.clip(rgb,0,65535)).astype(np.uint16);np.save(OUT/f'E2_{tag}_{method}_RGB16.npy',rgb);comp=bg*(1-mask[...,None])+rgb*mask[...,None];comp=np.rint(comp).astype(np.uint16);np.save(OUT/f'E2_{tag}_{method}_composite.npy',comp);Image.fromarray((comp>>8).astype('uint8')).save(OUT/f'E2_{tag}_{method}_moon.png');rep['probes'][tag+'_'+method]=dict(clipped_source_pixels=clipped,deep_delta_DN16=np.percentile((rgb.astype(float)-pere)[r<350],[1,5,50,95,99]).tolist())
save('E2_appearance.json',rep);print(rep['heldout_error_DN16'],rep['probes'],flush=True)
