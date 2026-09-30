from pathlib import Path
import json, io, numpy as np, tifffile as tf
from PIL import Image,ImageCms
O=Path('output/v57_integracio_20260913');a=tf.imread(O/'V57_native.tif');b=tf.imread(O/'V57_noSolar_native.tif')
report={}
for label,maskfn in [('inside520',lambda r:r<=520),('outside520',lambda r:r>520)]:
 n=c=s=mx=0
 for y in range(len(a)):
  m=maskfn(np.hypot(np.arange(a.shape[1])-5377,y-3777));d=np.abs(a[y,m].astype('int32')-b[y,m].astype('int32'));n+=len(d);c+=int(np.any(d>0,axis=1).sum());s+=int(d.sum());mx=max(mx,int(d.max()) if len(d) else 0)
 report[label]=dict(pixels=n,changed=c,max_DN16=mx,mean_DN16=s/(n*3))
print(report);(O/'C2_solar_ablation.json').write_text(json.dumps(report,indent=2))
with tf.TiffFile(O/'V57_native.tif') as t:icc=t.pages[0].tags[34675].value
im=Image.fromarray((b[3077:4477,4677:6077]>>8).astype('uint8'));im=ImageCms.profileToProfile(im,ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),outputMode='RGB');im.save(O/'vistes/V57_noSolar_moon.png')
