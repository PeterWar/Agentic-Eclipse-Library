from pathlib import Path
import json,numpy as np,tifffile as tf
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v63_encaix_contorn_20260913';A=R/'output/v62_prominencies_20260913/arrays'
rd=lambda i,c:np.load(A/f'V61_L{i:02d}_C{c}.npy').astype('float64')/65535
cur=tf.imread(O/'A1_default.tif').astype(float)/65535;hole=cur[...,3]<1;ba=rd(2,-1);bm=rd(2,-2);ma=rd(22,-1);mm=rd(22,-2);rgb=np.load(A/'C1_base_RGB16.npy').astype(float)/65535;has=np.max(rgb,axis=-1)>0
nativeB=tf.imread(O/'A1_base.tif').astype(float)/65535;nativeM=tf.imread(O/'A1_moon.tif').astype(float)/65535
rep=dict(nonopaque=int(hole.sum()),base_RGB_exists=int((hole&has).sum()),base_RGB_missing=int((hole&~has).sum()),Moon_alpha_one=int((hole&(ma==1)).sum()),Moon_alpha_not_one=int((hole&(ma<1)).sum()),base_alpha_one=int((hole&(ba==1)).sum()),base_alpha_not_one=int((hole&(ba<1)).sum()),ranges={})
for n,x in [('base_alpha',ba),('base_mask',bm),('moon_alpha',ma),('moon_mask',mm),('final_alpha',cur[...,3])]:rep['ranges'][n]=np.quantile(x[hole],[0,.01,.1,.5,.9,.99,1]).tolist()
proposed=bm.copy();hit=(mm*ma<1)&(mm*ma>0)&has&(ba==1)&(bm<1);proposed[hit]=1
np.save(O/'arrays/B1_base_validity_mask.npy',np.rint(proposed*65535).astype('uint16'))
rep['proposal']=dict(changed=int(hit.sum()),rule='Base has measured nonzero RGB and full source alpha under the existing partial lunar coverage; remove duplicate partial base display opacity there. Moon unchanged.',remaining_raw_coverage_holes=int(((1-(1-proposed*ba)*(1-mm*ma)<1)&(mm*ma>0)).sum()))
np.save(O/'arrays/B1_partial_transparency.npy',hole);(O/'B1_coverage.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep,indent=2),flush=True)
icc=ImageCms.ImageCmsProfile(str(R/'output/v62_prominencies_20260913/AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
for name,bb,k in [('top',(5245,3297,5310,3351),6),('bottom',(5080,4110,5320,4230),3),('west',(4900,3810,4990,4000),3)]:
 x0,y0,x1,y1=bb;sl=np.s_[y0-2777:y1-2777,x0-4377:x1-4377];rgbp=cur[sl][...,:3];alp=cur[sl][...,3:];w=(x1-x0)*k;h=(y1-y0)*k;pan=Image.new('RGB',(w*3,h+24));dr=ImageDraw.Draw(pan)
 for i,(label,bg) in enumerate([('V62 over black',np.zeros_like(rgbp)),('V62 over white',np.ones_like(rgbp)),('Transparency map',None)]):
  v=rgbp+(1-alp)*bg if bg is not None else np.repeat((1-alp),3,axis=2)
  im=ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(v,0,1)*255+.5)),icc,srgb,outputMode='RGB');pan.paste(im.resize((w,h),Image.Resampling.NEAREST),(i*w,24));dr.text((i*w+3,4),label,fill='white')
 pan.save(O/'vistes'/f'B1_{name}_transparency.png')
