from common60 import *
import tifffile as tf
from PIL import Image,ImageCms,ImageDraw
claim();prof=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));names=['V59_clean_native','V59_no_RHEF_native','V59_no_filters_native','V59_no_moon_native'];can=Image.new('RGB',(1800,1000),(25,25,25));dw=ImageDraw.Draw(can)
for col,n in enumerate(names):
 p=O/(n+'.tif');a=tf.imread(p);np.save(O/'arrays'/f'{n}_RGB_roi.npy',a[2777:4777,4377:6377,:3]);im=Image.fromarray((a[3077:4477,4677:6077,:3].astype('uint32')*255//65535).astype('uint8'));im=ImageCms.profileToProfile(im,prof,ImageCms.createProfile('sRGB'),outputMode='RGB');im.save(O/'vistes'/f'{n}_luna_1a1.png')
 for row,bb in enumerate([(4750,3530,5200,3980),(5150,3077,5600,3527)]):
  v=a[bb[1]:bb[3],bb[0]:bb[2],:3];im=Image.fromarray((v.astype('uint32')*255//65535).astype('uint8'));im=ImageCms.profileToProfile(im,prof,ImageCms.createProfile('sRGB'),outputMode='RGB');can.paste(im,(col*450,row*500+35));dw.text((col*450+4,row*500+8),n.replace('V59_','').replace('_native',''),fill='white')
can.save(O/'vistes/A3_ablacio_limbe_1a1.png');print('ABLATIONS',flush=True)
