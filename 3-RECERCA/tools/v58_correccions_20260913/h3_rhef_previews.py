from common58 import *
import tifffile as tf,io
from PIL import Image,ImageCms,ImageDraw
claim();can=Image.new('RGB',(1600,1000),(25,25,25));draw=ImageDraw.Draw(can)
for col,idx in enumerate([13,14,15,16]):
 p=O/f'V58P_RHEF_{idx}_native.tif';a=tf.imread(p)
 with tf.TiffFile(p) as t:icc=t.pages[0].tags[34675].value
 # Native400x450 top and western limb at100% filter opacity.
 for row,(x0,y0) in enumerate([(5177,3177),(4777,3577)]):
  v=a[y0:y0+450,x0:x0+400,:3];im=Image.fromarray((v.astype('uint32')*255//65535).astype('uint8'));im=ImageCms.profileToProfile(im,ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),outputMode='RGB');can.paste(im,(col*400,row*500+30));draw.text((col*400+5,row*500+8),f'RHEF{idx} 100% native1:1',fill='white')
can.save(O/'vistes/H3P_RHEF_all_limb_1a1.png')
