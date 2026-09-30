from pathlib import Path
import numpy as np,json,tifffile as tf
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';V=O/'vistes';old=tf.imread(O/'A2_clean_ROI.tif');new=tf.imread(O/'D2_artifact_pilot.tif');src=np.stack([np.load(A/f'L3_C{c}.npy') for c in range(3)],-1);fg=np.stack([np.load(A/f'L76_C{c}.npy') for c in range(3)],-1);support=np.any(src!=np.load(A/'B3_base_k0.9.npy'),-1)|np.any(fg!=np.load(A/'B10_L76_colour.npy'),-1);delta=new.astype('int32')-old.astype('int32');rep=dict(shape=new.shape,maxRGBchange=int(abs(delta[...,:3]).max()),maxAlphaChange=int(abs(delta[...,3]).max()),maxOutsideEdits=int(abs(delta[~support]).max()),changed_pixels=int(np.any(delta[...,:3],-1).sum()));print(rep)
# Correct only lost coverage from multiplying overlapping opacity ramps, no contour/mask/radius shift.
norm=new.astype(float)/65535;ma=np.load(A/'L30_C-2.npy')/65535;basem=np.load(A/'L3_C-2.npy')/65535;sel=(norm[...,3]>0)&(norm[...,3]<1)&(ma>0)&(basem>0);normalized=norm.copy();normalized[sel,:3]/=normalized[sel,3:];normalized[sel,3]=1
np.save(A/'D3_opacity_support.npy',sel);np.save(A/'D3_normalized_RGBA16.npy',np.rint(normalized*65535).astype('uint16'));rep['opacity_normalization']=dict(pixels=int(sel.sum()),minimum_original_alpha=float(norm[...,3][sel].min()),method='Renormalize only existing overlapping lunar/base coverage; RGB mixture ratios unchanged, no new boundary or radius. Original source masks untouched.');
icc=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
def view(a):
 z=a.astype(float)/65535;rgb=z[...,:3]+.12*(1-z[...,3:]);return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(rgb,0,1)*255+.5)),icc,srgb,outputMode='RGB')
for tag,bb,sc in [('full',(4730,3180,6010,4410),1),('top',(5245,3280,5310,3360),7),('bottom',(5060,4105,5320,4240),3)]:
 x0,y0,x1,y1=bb;sl=np.s_[y0-2777:y1-2777,x0-4377:x1-4377];w=(x1-x0)*sc;h=(y1-y0)*sc;pan=Image.new('RGB',(w*3,h+25));draw=ImageDraw.Draw(pan)
 for j,(label,a) in enumerate([('Pere V64',old),('Native colour + highlights',new),('Also coverage normalized',np.rint(normalized*65535).astype('uint16'))]):pan.paste(view(a[sl]).resize((w,h),Image.Resampling.NEAREST),(j*w,25));draw.text((j*w+4,5),label,fill='white')
 pan.save(V/f'D3_{tag}.png')
(O/'D3_pilot_review.json').write_text(json.dumps(rep,indent=2));assert rep['maxAlphaChange']==0;assert rep['maxOutsideEdits']<=2
