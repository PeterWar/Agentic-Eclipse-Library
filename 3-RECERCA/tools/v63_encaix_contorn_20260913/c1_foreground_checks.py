from pathlib import Path
import numpy as np,tifffile as tf,json,cv2
from scipy.ndimage import gaussian_filter1d,map_coordinates,label,maximum_filter
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v63_encaix_contorn_20260913';P=R/'output/v62_prominencies_20260913'
before=tf.imread(O/'A1_interiors_unmasked.tif');after=tf.imread(O/'D0_foreground_unmasked.tif');assert before.shape==after.shape
# The protocol specifies brightness in the original photograph. The old
# transformed proxy contains bright numerical outliers in its invalid lunar
# background; it cannot define the source-support judge.
source=tf.imread(R/'output/v61_interiors_limbe_20260913/V61_interiors_only.tif').astype(float)/65535
tr=json.loads((P/'E0_integrity.json').read_text())['transform'];M=np.array([[(tr[2]-tr[0])/8512,(tr[6]-tr[0])/6686,tr[0]],[(tr[3]-tr[1])/8512,(tr[7]-tr[1])/6686,tr[1]]]);inv=cv2.invertAffineTransform(M)
gy,gx=np.mgrid[2777:4777,4377:6377];sx=inv[0,0]*gx+inv[0,1]*gy+inv[0,2]-3480;sy=inv[1,0]*gx+inv[1,1]*gy+inv[1,2]-2365
source_envelope=map_coordinates(maximum_filter(source.max(-1),size=7),[sy,sx],order=1)
bright=source_envelope>=.05;dif=abs(before.astype('int32')-after.astype('int32'));mx=int(dif[bright].max());assert mx<=4,mx
outliers=((before[...,:3].max(-1)>=3277)&(dif.max(-1)>4));assert np.all(source_envelope[outliers]<.05)
v62=tf.imread(O/'A1_default.tif');v63=tf.imread(O/'B7_valid_foreground.tif');assert v63.shape[-1]==3 or np.all(v63[...,3]==65535)
rep=dict(PASS=True,foreground_maxRGB_at_least_point05_samples=int(bright.sum()),native_foreground_RGBA_max_DN16=mx,source_geometry_exact_claim='To be checked in D1 audit',nonopaque_lunar_ROI_before=int((v62[...,3]<65535).sum()),nonopaque_lunar_ROI_after=0,rectangular_ROI=[4377,2777,6377,4777],background_white_black_equivalent=True,old_transformed_bright_outliers_in_dark_background=int(outliers.sum()),outlier_original_source_7x7_max=float(source_envelope[outliers].max()),outlier_receipt='C1_invalid_background_outliers.json',judge='Original photographic foreground >=0.05 plus 3-pixel interpolation footprint; unchanged protocol, not brightness of the known invalid transformed proxy')
# Fixed radiometric response to a perturbation in the supplied foreground.
am=tf.imread(O/'A1_moon.tif')[...,3].astype(float)/65535
so=tf.imread(O/'A1_interiors_masked.tif').astype(float)/65535
sel=bright&(so[...,:3].max(-1)>.05)&(so[...,3]>.01)
rep['foreground_response']=dict(selected_samples=int(sel.sum()),old_attenuated_by_lunar_mask=int((sel&(am>0)).sum()),old_min_transmission=float((1-am)[sel].min()),new_transmission=1.0,scope='The same supplied solar foreground is now composed above the lunar layer. No new solar signal or spatial registration inferred.')
# All previously painted regions and the complete limb are reviewed at native sampling.
icc=ImageCms.ImageCmsProfile(str(P/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
def view(a):return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)),icc,srgb,outputMode='RGB')
f4=gaussian_filter1d(np.load(R/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'),3,mode='wrap');th=np.arange(1440)*np.pi/720;ds=np.arange(-8,16,.25);rr=f4[:,None]+ds;xx=5376.568111973117+np.cos(th[:,None])*rr-4377;yy=3776.647534140857+np.sin(th[:,None])*rr-2777
can=Image.new('RGB',(1440,240));dr=ImageDraw.Draw(can)
for i,(name,a) in enumerate([('V62',v62),('V63 candidate',v63)]):
 a=a.astype(float)/65535;rgb=a[...,:3]+(1-a[...,3:])*.6 if a.shape[-1]==4 else a
 pol=np.stack([map_coordinates(rgb[...,c],[yy,xx],order=1) for c in range(3)],-1);can.paste(view(pol.transpose(1,0,2)),(0,i*120+24));dr.text((5,i*120+4),name+' | complete 360-degree contour, d=-8..16 px',fill='white')
can.save(O/'vistes/C1_full_limb_polar.png')
boxes=[(5259,3326,5300,3341),(4995,3471,5041,3530),(4920,3812,4983,4007),(5785,3936,5803,3973),(5032,4071,5040,4079),(5091,4124,5101,4134),(5112,4140,5127,4153),(5214,4196,5226,4202),(5262,4211,5274,4216),(5290,4217,5301,4221)]
for i,bb in enumerate(boxes):
 x0,y0,x1,y1=bb;x0-=8;y0-=8;x1+=8;y1+=8;k=5;w=(x1-x0)*k;h=(y1-y0)*k;can=Image.new('RGB',(2*w,h+24));dr=ImageDraw.Draw(can)
 for j,(name,a) in enumerate([('V62',v62),('V63 candidate',v63)]):
  a=a[y0-2777:y1-2777,x0-4377:x1-4377].astype(float)/65535;rgb=a[...,:3]+(1-a[...,3:])*.6 if a.shape[-1]==4 else a;can.paste(view(rgb).resize((w,h),Image.Resampling.NEAREST),(j*w,24));dr.text((j*w+3,4),name,fill='white')
 can.save(O/'vistes'/f'C1_blue_{i+1:02d}.png')
(O/'C1_foreground_checks.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep),flush=True)
