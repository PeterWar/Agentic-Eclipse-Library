from common58 import *
import tifffile as tf,io
from PIL import Image,ImageCms
claim();rep={}
for name in ['V58O_default_native','V58O_solar_composite_native','V58O_11_12_moon_native']:
 a=tf.imread(O/f'{name}.tif');print(name,a.shape,a.dtype,flush=True);rep[name]=dict(shape=a.shape,dtype=str(a.dtype))
 with tf.TiffFile(O/f'{name}.tif') as t:icc=t.pages[0].tags[34675].value
 for tag,v,size in [('full',a,(1583,1126)),('limb_1a1',a[3077:4477,4677:6077],None)]:
  rgb=(v[...,:3].astype('uint32')*255//65535).astype('uint8');im=Image.fromarray(rgb);im=ImageCms.profileToProfile(im,ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),outputMode='RGB')
  if v.shape[2]==4:
   bg=Image.new('RGB',im.size,(30,30,30));bg.paste(im,(0,0),Image.fromarray((v[...,3]//257).astype('uint8')));im=bg
  if size:im.thumbnail(size,Image.Resampling.LANCZOS)
  im.save(O/'vistes'/f'G5P_{name}_{tag}.png')
save('G5P_native_tiff_info.json',rep)
