from common61 import *
import tifffile as tf
from scipy.ndimage import label,find_objects
from PIL import Image,ImageCms,ImageDraw
claim();rows=json.loads((O/'A0_sources.json').read_text());D=O/'arrays'
def rd(key,i,c):
 p=D/f'{key}_L{i:02d}_C{c}.npy';return np.load(p).astype('float32')/65535 if p.exists() else None
def rgb(key,i):return np.stack([rd(key,i,c) for c in range(3)],-1)
def outview(a,name):
 im=Image.fromarray(np.uint8(np.clip(a,0,1)*255));im=ImageCms.profileToProfile(im,ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc')),ImageCms.createProfile('sRGB'),outputMode='RGB');im.save(O/'vistes'/name);return im
ref=tf.imread(O/'Vista_V57_reference.tif')[...,:3].astype('float32')/65535;renderings={};rep={}
for color,mask in [('V57','V57'),('V60','V60'),('V57','V60'),('V60','V57')]:
 out=np.zeros((2000,2000,3),np.float32)
 for i in range(7):
  a=rd(color,i,-1);m=rd(mask,i,-2)
  if a is None:a=np.ones((2000,2000),np.float32)
  if m is not None and not rows[mask]['layers'][i]['mask_flags']['mask_disabled']:a=a*m
  a*=rows[color]['layers'][i]['opacity']/255
  out+=a[...,None]*(rgb(color,i)-out)
 key=f'RGB{color}_MASK{mask}';renderings[key]=out;np.save(D/(key+'.npy'),out)
 yy,xx=np.ogrid[2777:4777,4377:6377];rr=np.hypot(xx-5376.5681,yy-3776.6475);edge=(rr>430)&(rr<480);sel=edge&(ref[...,0]>.4)&(ref[...,0]>ref[...,2]*1.2)
 delta=abs(out-ref)*65535;rep[key]={'mean_edge_DN':float(delta[edge].mean()),'p99_edge_DN':float(np.quantile(delta[edge],.99)),'mean_protected_DN':float(delta[sel].mean()),'protected_pixels':int(sel.sum())}
 outview(out[650:1200,450:700],key+'_west.png')
can=Image.new('RGB',(1250,590),(30,30,30));draw=ImageDraw.Draw(can)
for k,(n,a) in enumerate([('Vista V57',ref)]+list(renderings.items())):
 im=outview(a[650:1200,450:700],'temp_'+str(k)+'.png');can.paste(im,(250*k,40));draw.text((250*k+5,8),n,fill='white')
can.save(O/'vistes/A2_inner_factorial.png')
save('A2_inner_factorial.json',rep);print(json.dumps(rep,indent=2))
# User's new blue annotations are layer30, not the hidden previous layer31.
a=rd('V60',30,-1);b=rgb('V60',30);sel=(a>.03)&(b[...,2]>.2)&(b[...,2]>b[...,0]*1.4)&(b[...,2]>b[...,1]*1.3);lab,n=label(sel);marks=[]
for j,sl in enumerate(find_objects(lab),1):
 y,x=np.nonzero(lab[sl]==j)
 if len(x)<4:continue
 y+=sl[0].start;x+=sl[1].start;marks.append({'pixels':len(x),'bbox':[int(x.min()+4377),int(y.min()+2777),int(x.max()+4378),int(y.max()+2778)]})
save('A2_blue_marks.json',marks);print(marks)
