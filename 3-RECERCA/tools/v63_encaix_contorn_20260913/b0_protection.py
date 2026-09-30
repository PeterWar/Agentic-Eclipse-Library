from pathlib import Path
import json,numpy as np,tifffile as tf
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v63_encaix_contorn_20260913';P=R/'output/v62_prominencies_20260913';A=P/'arrays'
meta=json.loads((P/'E0_integrity.json').read_text())['metadata']
def rd(i,c):return np.load(A/f'V61_L{i:02d}_C{c}.npy').astype('float64')/65535
def native(n):
 a=tf.imread(O/f'A1_{n}.tif').astype('float64')/65535
 return a[...,:3],a[...,3] if a.shape[-1]==4 else np.ones(a.shape[:2])
base,ab=native('base');so,aso=native('interiors_masked');moon,am=native('moon');ref,_=native('default')
rgbbase=np.divide(base,ab[...,None],out=np.zeros_like(base),where=ab[...,None]>0)
pm=np.load(R/'output/v60_marques_v59_20260913/arrays/C2_prominence_protection.npy')
user=np.load(A/'D0_user_mask_normalized.npy')[2777:4777,4377:6377].astype('float64')/65535
base_m=rd(2,-2);wl=np.load(R/'output/v60_marques_v59_20260913/arrays/C2_lunar_protection.npy')
newm={};rows=[]
for i in range(3,9):
 m=rd(i,-2);pre=np.divide(m,1-pm,out=np.ones_like(m),where=pm<1-1e-6);pre=np.clip(pre,0,1)
 # The V61 change already establishes full mask response at the lunar edge.
 pre[(wl<1)&(base_m>0)]=1
 # Replacement only in the user's existing prominence selection. No new region.
 n=m+(pre-m)*user;newm[i]=n;np.save(O/'arrays'/f'B0_L{i:02d}_mask.npy',np.rint(n*65535).astype('uint16'))
 rows.append(dict(id=meta[i]['id'],changed=int(np.count_nonzero(np.rint(n*65535)!=np.rint(m*65535))),outside_user_exact=bool(np.array_equal(m[user==0],n[user==0]))))
def render(change):
 b=rgbbase.copy()
 for i in range(3,10):
  a=rd(i,-1)*((newm[i] if change and i in newm else rd(i,-2)))*meta[i]['opacity']/255;f=rd(i,1)[...,None]
  res=b*f if meta[i]['blend']=='BlendMode.MULTIPLY' else np.where(b<.5,2*b*f,1-2*(1-b)*(1-f))
  b+=(res-b)*a[...,None]
 b*=ab[...,None];b=so+(1-aso[...,None])*b;b=moon+(1-am[...,None])*b
 return b
old=render(False);new=render(True);err=abs(old-ref)*65535
print('MODEL ERR',np.quantile(err,[.5,.99,.999,1]),flush=True)
np.save(O/'arrays/B0_model_old.npy',old);np.save(O/'arrays/B0_model_new.npy',new)
pilot=np.clip(ref+new-old,0,1);np.save(O/'arrays/B0_native_delta_pilot.npy',pilot)
icc=ImageCms.ImageCmsProfile(str(P/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
for name,bb,k in [('top',(5245,3297,5310,3351),6),('west',(4870,3720,4970,3970),3),('NW',(4970,3460,5050,3550),4),('SE',(5770,3910,5820,3990),4),('bottom',(5080,4110,5320,4230),3)]:
 x0,y0,x1,y1=bb;w=(x1-x0)*k;h=(y1-y0)*k;pan=Image.new('RGB',(w*2,h+25));dr=ImageDraw.Draw(pan)
 for j,(n,a) in enumerate([('V62',ref),('B0 old protection removed in user selection',pilot)]):
  im=Image.fromarray(np.uint8(np.clip(a[y0-2777:y1-2777,x0-4377:x1-4377],0,1)*255+.5));im=ImageCms.profileToProfile(im,icc,srgb,outputMode='RGB');pan.paste(im.resize((w,h),Image.Resampling.NEAREST),(j*w,25));dr.text((j*w+4,5),n,fill='white')
 pan.save(O/'vistes'/f'B0_{name}.png')
(O/'B0_protection.json').write_text(json.dumps(dict(model_error_DN16=np.quantile(err,[.5,.99,.999,1]).tolist(),masks=rows,scope='Exploratory causal ablation; no mask promoted',geometry_change=False,source_photography_exact=True),indent=2)+'\n')
