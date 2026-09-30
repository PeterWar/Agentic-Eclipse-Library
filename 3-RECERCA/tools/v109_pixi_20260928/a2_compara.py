from pathlib import Path
import sys,json,io
import numpy as np, tifffile, cv2
from PIL import Image,ImageCms
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[3]; O=ROOT/'4-RESULTATS/v109_pixi_20260928'
sys.path.insert(0,str(ROOT/'3-RECERCA/tools/v71_marques_v69_20260916'))
from psb69 import PSB
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V109_PIXI_I_ARTEFACTES_20260928'
P=PSB(str(O/'entrades/pixi_capes.psb')); B=PSB(str(ROOT/'1-PHOTOSHOP/V108.psb'))
print('PIXI layers',P.layers,flush=True)
C=B.composite()[...,:3]; T=tifffile.imread(O/'entrades/pixi_sense_marques.tif')[...,:3]
np.save(O/'entrades/V108_compost.npy',C); np.save(O/'entrades/PIXI_net.npy',T)
with tifffile.TiffFile(O/'entrades/pixi_sense_marques.tif') as tf:icc=tf.pages[0].tags[34675].value
(O/'entrades/AdobeRGB.icc').write_bytes(icc)
trans=ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),'RGB','RGB')
def save_view(a,name):
 a=cv2.resize(a,(2000,round(a.shape[0]*2000/a.shape[1])),interpolation=cv2.INTER_AREA)
 img=Image.fromarray(np.uint8(np.clip(a/257,0,255)));ImageCms.applyTransform(img,trans).save(O/'vistes'/name)
save_view(C,'V108.png');save_view(T,'PIXI_net.png');save_view(P.composite()[...,:3],'PIXI_marcat.png')
D=np.any(C!=T,axis=2);dif=np.max(np.abs(C.astype(np.int32)-T.astype(np.int32)),axis=2)
np.save(O/'entrades/delta_mask.npy',D)
mark=P.channel_box(307,-1,(0,0,P.width,P.height));np.save(O/'entrades/marques_alfa.npy',mark)
Image.fromarray(np.uint8(cv2.resize(mark.astype(np.float32),(2000,1423))/257)).save(O/'vistes/marques_alfa.png')
Image.fromarray(np.uint8(cv2.resize(np.log1p(dif.astype(np.float32))/np.log(65536),(2000,1423))*255)).save(O/'vistes/delta_log.png')
labels,n=ndimage.label(mark>1000);regs=[]
for i,s in enumerate(ndimage.find_objects(labels),1):
 if s is None:continue
 mask=labels[s]==i;area=int(mask.sum())
 if area<50:continue
 regs.append({'id':i,'n':area,'box':[s[1].start,s[0].start,s[1].stop,s[0].stop],'alpha_max':int(mark[s][mask].max())})
ys,xs=np.where(D)
report={'shape':list(C.shape),'changed_pixels':int(D.sum()),'fraction':float(D.mean()),'bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'max_DN':int(dif.max()),'percentiles_DN':np.percentile(dif,[0,50,90,95,99,99.9,100]).tolist(),'counts_by_DN':{str(k):int((dif>k).sum()) for k in [0,1,2,4,8,16,32,64,128,512,2048]},'marks':regs}
# A raster belonging to Pixi's base is useful to separate pre-existing conversion from the manual blend.
L=P.channel_box(244,0,(0,0,P.width,P.height));report['pixi_base_R_vs_V108']={'changed':int(np.count_nonzero(L!=C[...,0])),'max_DN':int(np.max(np.abs(L.astype(np.int32)-C[...,0].astype(np.int32))))}
with (O/'COMPARACIO_INICIAL.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report,indent=2),flush=True)
