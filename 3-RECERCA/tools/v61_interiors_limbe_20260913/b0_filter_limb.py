from common61 import *
import tifffile as tf
from scipy.ndimage import map_coordinates,distance_transform_edt
from PIL import Image,ImageCms,ImageDraw
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
claim();rows=json.loads((O/'A0_sources.json').read_text())['V60']['layers'];D=O/'arrays'
def rd(i,c):
 p=D/f'V60_L{i:02d}_C{c}.npy';return np.load(p).astype('float32')/65535 if p.exists() else None
def render(skip=[],override={}):
 out=np.zeros((2000,2000,3),np.float32)
 for i,l in enumerate(rows[:30]):
  if i in skip or not l['visible']:continue
  f=np.stack([rd(i,c) for c in range(3)],-1) if i<11 or i>26 else np.repeat(rd(i,1)[...,None],3,-1)
  a=rd(i,-1);a=np.ones((2000,2000),np.float32) if a is None else a;m=rd(i,-2)
  if m is not None:a*=m
  if i in override:f,a=override[i]
  a*=l['opacity']/255
  mode=l['blend'];res=f if mode=='BlendMode.NORMAL' else np.maximum(out,f) if mode=='BlendMode.LIGHTEN' else out*f if mode=='BlendMode.MULTIPLY' else np.where(out<.5,2*out*f,1-2*(1-out)*(1-f)) if mode=='BlendMode.OVERLAY' else None
  assert res is not None,mode
  out+=a[...,None]*(res-out)
 return out
base=render(skip=list(range(11,27)));allf=render();np.save(D/'B0_model.npy',allf);native=tf.imread(O/'V60_clean.tif')[2777:4777,4377:6377,:3]/65535;print('Model DN',np.quantile(abs(allf-native)*65535,[.5,.99,1]))
variants=[('V60',allf),('Sense filtres',base),('Sense ACHF',render(skip=[17]))]+[(f'Només {i}',render(skip=[j for j in range(11,27) if j!=i])) for i in range(11,17)]
can=Image.new('RGB',(700,150*len(variants)),(25,25,25));d=ImageDraw.Draw(can);pr=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'))
for k,(n,a) in enumerate(variants):
 im=Image.fromarray(np.uint8(np.clip(a[485:600,750:1450],0,1)*255));im=ImageCms.profileToProfile(im,pr,ImageCms.createProfile('sRGB'),outputMode='RGB');can.paste(im,(0,k*150+25));d.text((8,k*150+5),n,fill='white')
can.save(O/'vistes/B0_top_ablations.png')
theta=np.linspace(-100,-75,101)*np.pi/180;rad=np.arange(445,490,.25);yy=3776.6475+np.sin(theta[:,None])*rad[None,:]-2777;xx=5376.5681+np.cos(theta[:,None])*rad[None,:]-4377
fig,ax=plt.subplots(3,1,figsize=(11,9),sharex=True)
for i in range(11,18):
 f=rd(i,1);m=rd(i,-2);v=np.median(map_coordinates(f,[yy,xx],order=1),axis=0);a=np.median(map_coordinates(m,[yy,xx],order=1),axis=0);ax[0].plot(rad,v,label=str(i));ax[1].plot(rad,a,label=str(i));ax[2].plot(rad,1-rows[i]['opacity']/255*a*(1-v),label=str(i))
for a,n in zip(ax,['Filter raster','Mask','Multiplying gain (17 overlay excluded)']):a.set_ylabel(n);a.legend(ncol=7);a.grid()
ax[-1].set_xlabel('Radius in unchanged canvas (pixels)');fig.tight_layout();fig.savefig(O/'vistes/B0_top_profiles.png');plt.close(fig)
