from pathlib import Path
import tifffile as tf, numpy as np, json
from PIL import Image,ImageCms
R=Path.cwd();O=R/'output/v63_encaix_contorn_20260913'
p=O/'V63_candidate.tif'
with tf.TiffFile(p) as f:
    page=f.pages[0]
    print('TIFF',page.shape,page.extrasamples,flush=True)
    a=page.asarray()[::6,::6].astype('float32')/65535
rgb=a[...,:3]
if a.shape[-1]==4:
    yy,xx=np.indices(a.shape[:2]);bg=np.where(((xx//16+yy//16)%2)[...,None],.45,.55)
    rgb=rgb+(1-a[...,3:])*bg
icc=ImageCms.ImageCmsProfile(str(R/'output/v62_prominencies_20260913/AdobeRGB.icc'))
im=Image.fromarray(np.uint8(np.clip(rgb,0,1)*255+.5))
ImageCms.profileToProfile(im,icc,ImageCms.createProfile('sRGB'),outputMode='RGB').save(O/'vistes/V63_full_canvas.png')
print('FULL PREVIEW COMPLETE',flush=True)
