from pathlib import Path
import json, io
import numpy as np
import tifffile as tf
from PIL import Image,ImageCms
R=Path('/Users/USUARI/Downloads/Eclipse 2026'); O=R/'output/v57_integracio_20260913'
a=tf.imread(O/'V42_native.tif'); b=tf.imread(O/'V57_native.tif')
with tf.TiffFile(O/'V57_native.tif') as f:icc=f.pages[0].tags[34675].value
print('PROFILE',ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))),flush=True)
def save(arr,name,size=None):
 im=Image.fromarray((arr.astype(np.uint32)*255//65535).astype('uint8'))
 if size:im.thumbnail(size,Image.Resampling.LANCZOS)
 im=ImageCms.profileToProfile(im,ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),outputMode='RGB')
 im.save(O/'vistes'/name)
for n,c in [('V42',a),('V57',b)]:
 save(c,f'{n}_full.png',(1583,1126));save(c[3077:4477,4677:6077],f'{n}_moon_1a1.png')
# Per-row metrics avoid 1 GB full-image temporaries.
regions={n:{'pixels':0,'changed_gt3':0,'abs_sum':0,'max':0} for n in ['r_le_435','435_520','520_900','r_gt_900']}
for y in range(b.shape[0]):
 rr=np.hypot(np.arange(b.shape[1])-5377,y-3777)
 d=np.abs(b[y].astype('int32')-a[y].astype('int32'))
 for n,m in [('r_le_435',rr<=435),('435_520',(rr>435)&(rr<=520)),('520_900',(rr>520)&(rr<=900)),('r_gt_900',rr>900)]:
  v=d[m];z=regions[n];z['pixels']+=len(v);z['changed_gt3']+=int(np.any(v>3,axis=1).sum());z['abs_sum']+=int(v.sum());z['max']=max(z['max'],int(v.max()) if len(v) else 0)
for z in regions.values():z['mean_abs_DN16']=z.pop('abs_sum')/(3*z['pixels'])
ref=tf.imread(R/'output/earthshine_v56_three_routes_20260913/staging/Photoshop_V56_readback_RGBA.tif')[3077:4477,4677:6077]
d=np.abs(b[3077:4477,4677:6077].astype('int32')-ref[...,:3].astype('int32'))
y,x=np.mgrid[:1400,:1400];m=np.hypot(x-700,y-700)<=435
rep=dict(comparison_V42=regions,moon_r435_V56_native={'max_DN16':int(d[m].max()),'p99_DN16':float(np.percentile(d[m],99))},profile=ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))))
(O/'C1_visual_metrics.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep),flush=True)
