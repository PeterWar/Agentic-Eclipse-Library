from common61 import *
import tifffile as tf
from PIL import Image,ImageCms,ImageDraw
claim();D=O/'arrays';rows=json.loads((O/'A0_sources.json').read_text())['V60']['layers']
def rd(i,c):
 p=D/f'V60_L{i:02d}_C{c}.npy';return np.load(p).astype('float32')/65535 if p.exists() else None
base=rd(9,-2);pm=np.load(R/'output/v60_marques_v59_20260913/arrays/C2_prominence_protection.npy');wl=np.load(R/'output/v60_marques_v59_20260913/arrays/C2_lunar_protection.npy');hit=(wl<1)&(base>0);report={};old=np.zeros((2000,2000,3),np.float32);new=old.copy()
for i,l in enumerate(rows[:30]):
 if not l['visible']:continue
 rgb=np.stack([rd(i,c) for c in range(3)],-1) if i<11 or i>26 else np.repeat(rd(i,1)[...,None],3,-1)
 a=rd(i,-1);a=np.ones(base.shape,np.float32) if a is None else a;m=rd(i,-2);an=a.copy()
 if m is not None:
  mn=m.copy()
  if 11<=i<=16:
   mn[hit]=(1-pm)[hit];np.save(D/f'B1_L{i:02d}_mask.npy',np.rint(mn*65535).astype('uint16'));report[str(i)]={'changed_pixels':int(np.sum(mn!=m)),'raster_exact':True,'outside_hit_exact':bool(np.array_equal(mn[~hit],m[~hit]))}
  a*=m;an*=mn
 for out,aa in [(old,a),(new,an)]:
  mode=l['blend'];res=rgb if mode=='BlendMode.NORMAL' else np.maximum(out,rgb) if mode=='BlendMode.LIGHTEN' else out*rgb if mode=='BlendMode.MULTIPLY' else np.where(out<.5,2*out*rgb,1-2*(1-out)*(1-rgb))
  out+=aa[...,None]*(l['opacity']/255)*(res-out)
native=tf.imread(O/'V60_clean.tif')[2777:4777,4377:6377,:3]/65535;new=np.clip(native+new-old,0,1);np.save(D/'B1_model.npy',new)
can=Image.new('RGB',(1400,700),(25,25,25));d=ImageDraw.Draw(can);p=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'))
for k,(n,a) in enumerate([('V60 - alpha applied twice',native),('B1 - single coverage',new)]):
 im=Image.fromarray(np.uint8(a[450:1100,650:1350]*255));im=ImageCms.profileToProfile(im,p,ImageCms.createProfile('sRGB'),outputMode='RGB');can.paste(im,(700*k,40));d.text((700*k+5,10),n,fill='white')
can.save(O/'vistes/B1_single_coverage.png')
edge=hit&(base<1)&(pm<.001);q=np.linspace(.05,.95,19);K=.4;pct=.4;before=1-pct*q*(1-K);after=np.full(q.shape,1-pct*(1-K));report['constant_filter_control']={'expected_gain':.76,'before_gain_range':np.ptp(before),'after_gain_range':np.ptp(after),'edge_pixels':int(edge.sum()),'scope':'known alpha-composition algebra; not new astronomical detail','PASS':bool(np.ptp(after)==0)};save('B1_single_coverage.json',report);print(report)
