from common60 import *
import tifffile as tf,io
from scipy.ndimage import label,find_objects
from PIL import Image,ImageCms,ImageDraw
claim();D=O/'arrays';rgb=np.load(D/'MARK_RGB.npy');a=np.load(D/'MARK_ALPHA.npy');bb=np.load(D/'MARK_BBOX.npy');x0,y0,x1,y1=bb;v=rgb.astype('float32')/65535
colors={'verd':(v[...,1]>.25)&(v[...,1]>v[...,0]*1.5)&(v[...,1]>v[...,2]*1.5),'lila':(v[...,0]>.15)&(v[...,2]>.15)&(v[...,1]<v[...,0]*.6),'blau':(v[...,2]>.3)&(v[...,0]<v[...,2]*.5)&(v[...,1]<v[...,2]*.7)};rows=[]
for name,sel in colors.items():
 sel &= a>2000;lab,n=label(sel)
 for j,sl in enumerate(find_objects(lab),1):
  if sl is None:continue
  yy,xx=np.nonzero(lab[sl]==j)
  if len(xx)<8:continue
  yy=yy+sl[0].start+y0;xx=xx+sl[1].start+x0;rows.append(dict(color=name,n=int(len(xx)),bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],center=[float(xx.mean()),float(yy.mean())],r_sun=[float(np.hypot(xx-CX,yy-CY).min()),float(np.hypot(xx-CX,yy-CY).max())]));np.save(D/f'mark_{name}_{j}_xy.npy',np.stack([xx,yy],1))
save('A2_marks.json',rows);print(rows,flush=True)
p=O/'V59_marked_native.tif';imdata=tf.imread(p);prof=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'))
def convert(ar):return ImageCms.profileToProfile(Image.fromarray((ar[...,:3].astype('uint32')*255//65535).astype('uint8')),prof,ImageCms.createProfile('sRGB'),outputMode='RGB')
convert(imdata[::7,::7]).save(O/'vistes/V59_marques_llenc.png');convert(imdata[3077:4477,4677:6077]).save(O/'vistes/V59_marques_luna_1a1.png');print('MARKED_VIEWS',flush=True)
