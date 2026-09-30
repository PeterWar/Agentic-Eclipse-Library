from common58 import *
import tifffile as tf,io
from PIL import Image,ImageCms,ImageDraw
claim();V=O/'vistes';V.mkdir(exist_ok=True)
def convert(a,p):
 with tf.TiffFile(p) as t:icc=t.pages[0].tags[34675].value
 im=Image.fromarray((a[...,:3].astype('uint32')*255//65535).astype('uint8'))
 return ImageCms.profileToProfile(im,ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),outputMode='RGB')
can=Image.new('RGB',(1600,1000),(25,25,25));draw=ImageDraw.Draw(can);base=tf.imread(O/'V58E_base_native.tif');w=np.load(O/'prepared_layers/RHEF_protection_weight.npy')[400:1600,400:1600];rep={'native_enabled_mask_effect':{},'all_filters_reviewed':list(range(11,27))}
for col,idx in enumerate([13,14,15,16]):
 p=O/f'V58E_filter_{idx}_native.tif';a=tf.imread(p);im=convert(a,p)
 for row,(x,y) in enumerate([(400,0),(0,400)]):
  can.paste(im.crop((x,y,x+400,y+450)),(col*400,row*500+30));draw.text((col*400+5,row*500+8),f'RHEF{idx} 100% mask ACTIVE native1:1',fill='white')
 d=np.abs(a[...,:3].astype('int32')-base[...,:3].astype('int32'));protected=w==0;mx=int(d[protected].max());assert mx<=3,(idx,mx);rep['native_enabled_mask_effect'][str(idx)]={'fully_protected_pixels':int(protected.sum()),'max_filter_contribution_DN16':mx,'whole_ROI_max_DN16':int(d.max())}
can.save(V/'H7_RHEF_enabled_limb_1a1.png')
for group,ids in enumerate([list(range(11,19)),list(range(19,27))]):
 c=Image.new('RGB',(1600,1000),(25,25,25));dw=ImageDraw.Draw(c)
 for k,i in enumerate(ids):
  p=O/f'V58E_filter_{i}_native.tif';im=convert(tf.imread(p),p);c.paste(im.crop((0,400,400,850)),((k%4)*400,(k//4)*500+30));dw.text(((k%4)*400+5,(k//4)*500+8),f'L{i} 100% native1:1',fill='white')
 c.save(V/f'H7_all_filters_west_{group}_1a1.png')
p=O/'V58E_default_native.tif';a=tf.imread(p);im=convert(a[3177:4377,4777:5977],p);im.save(V/'V58_luna_1a1.png');im=convert(a[::7,::7],p);im.save(V/'V58_conjunt.png');save('H7_native_mask_QA.json',rep);print('MASK_QA_PASS',flush=True)
