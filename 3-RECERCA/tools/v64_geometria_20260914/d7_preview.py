from pathlib import Path
import numpy as np,tifffile as tf,json
from PIL import Image,ImageCms
R=Path.cwd();O=R/'output/v64_geometria_20260914';V=O/'vistes'
a=tf.imread(O/'V64_candidate.tif');icc=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
q=a[::4,::4].astype('float32')/65535
if q.shape[-1]==4:q=q[...,:3]+.15*(1-q[...,3:])
im=ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(q,0,1)*255+.5)),icc,srgb,outputMode='RGB');im.thumbnail((1800,1400));im.save(V/'V64_full_canvas.png')
copy=tf.imread(O/'A0_extra12_masked.tif');clean=tf.imread(O/'A0_clean.tif');without=tf.imread(O/'A0_without_extra12.tif');assert not copy.any() and np.array_equal(clean,without)
(O/'D7_copy_no_effect.json').write_text(json.dumps(dict(original_layer83_masked_native_RGBA_max_DN16=0,native_with_without_layer83_max_DN16=0,copy_geometry_diagnostic='C6/C7 estimates refer only to unmasked same-photo comparison. The existing mask removes this layer completely from the lunar ROI, so its geometric offset cannot explain the visible defects.',correction_promoted=False,attempts_D4_and_D4c='Abandoned and fully undone; empty bounding box was due to the original masking, not a proven Photoshop conversion defect. Source83 retained exactly.'),indent=2)+'\n')
print('PREVIEW COMPLETE')
