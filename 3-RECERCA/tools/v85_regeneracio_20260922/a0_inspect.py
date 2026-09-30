from pathlib import Path
import sys,json,io,struct,numpy as np,cv2
from PIL import Image,ImageCms,ImageDraw
R=Path(__file__).resolve().parents[3];O=R/'4-RESULTATS/v85_regeneracio_20260922';sys.path.insert(0,str(R/'3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
from psd_tools.psd.image_resources import ImageResources
from psd_tools.constants import Resource
P=O/'V84_Pere_input.psb';p=PSB(str(P));box=(4600,3000,6150,4550);records=[]
with P.open('rb') as f:
 f.seek(26);n=struct.unpack('>I',f.read(4))[0];f.seek(n,1);icc=ImageResources.read(f).get_data(Resource.ICC_PROFILE)
prof=ImageCms.ImageCmsProfile(io.BytesIO(icc));dst=ImageCms.createProfile('sRGB')
def rgbim(a):return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,65535)/257)),prof,dst,outputMode='RGB')
def layer(lid):
 L=p.layer(lid);data={};rgb=[]
 for cid in [0,1,2,-1,-2]:
  if cid in L['chans']:
   v=p.channel_box(lid,cid,box,fill=65535 if cid==-2 and L['mask']['background']==255 else 0);data['c'+str(cid)]=v
   if cid in [0,1,2]:rgb.append(v)
 if len(rgb)==3:data['RGB']=np.stack(rgb,axis=-1)
 data['box']=np.array(box);np.savez_compressed(O/f'ROI_L{lid}.npz',**data);records.append(L)
 return data
base=layer(3);moon=layer(30);marks=layer(251);limb=layer(246)
for lid in [41,42,47,49,51,54,55,56,250,234]:layer(lid)
for lid,a in [(3,base),(251,marks),(246,limb)]:
 rgb=a['RGB'].astype(np.float32);alpha=a.get('c-1',np.full(rgb.shape[:2],65535,np.uint16)).astype(np.float32)/65535
 if lid!=3:rgb=rgb*alpha[...,None]+12000*(1-alpha[...,None])
 rgbim(rgb).save(O/f'ROI_L{lid}.png')
for lid,a in [(251,marks),(246,limb)]:
 alpha=a['c-1'].astype(np.float32)/65535;comp=base['RGB']*(1-alpha[...,None])+a['RGB']*alpha[...,None];rgbim(comp).save(O/f'base_amb_marques_{lid}.png')
# Full-frame base view with marks, plus separate clean base.
small=[]
for cid in [0,1,2]:
 v,org=p.channel(3,cid);small.append(cv2.resize(v,(1600,round(p.height*1600/p.width)),interpolation=cv2.INTER_AREA))
full=np.stack(small,-1);im=rgbim(full);im.save(O/'base_llenc_complet.png');dr=ImageDraw.Draw(im);scale=1600/p.width;dr.rectangle(tuple(int(z*scale) for z in box),outline='red',width=2);im.save(O/'base_localitzacio_roi.png')
(O/'LAYERS.json').write_text(json.dumps(p.layers,ensure_ascii=False,indent=2));print('READY',O)
