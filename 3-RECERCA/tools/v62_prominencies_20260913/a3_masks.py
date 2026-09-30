from pathlib import Path
import json,numpy as np,tifffile
from PIL import Image,ImageCms,ImageDraw
from scipy.ndimage import label,find_objects
R=Path.cwd();O=R/'output/v62_prominencies_20260913';A=O/'arrays';P=R/'output/v61_interiors_limbe_20260913/arrays'
load=lambda i,c:np.load(A/f'V61_L{i:02d}_C{c}.npy').astype('float32')/65535
moon=np.stack([load(22,c) for c in range(3)],-1);lm=load(22,-2);old=np.load(P/'V60_L29_C-2.npy').astype('float32')/65535;sm=load(19,-2);s=np.stack([load(19,c) for c in range(3)],-1)
bg=tifffile.imread(O/'V61_no_interiors.tif').astype('float32')/65535
assert bg.shape[-1]==4
# Reconstruct premultiplied corona from the measured native ablation wherever observable.
cor=(bg[...,:3]-moon*lm[...,None])/np.maximum(1-lm[...,None],1e-12)
ca=(bg[...,3]-lm)/np.maximum(1-lm,1e-12)
soalpha=sm*load(19,-1)
inner=s*soalpha[...,None]+cor*(1-soalpha[...,None]);ia=soalpha+ca*(1-soalpha)
pred=moon*lm[...,None]+inner*(1-lm[...,None]);native=tifffile.imread(O/'V61_clean.tif')[...,:3]/65535
ok=lm<.99;error=np.max(abs(pred-native)[ok])*65535
print('composition reproduction maxDN',error)
restore=moon*old[...,None]+inner*(1-old[...,None])
src=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));dst=ImageCms.createProfile('sRGB')
def cv(q):return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(q,0,1)*255)),src,dst,outputMode='RGB')
def panel(n,bb):
 x0,y0,x1,y1=bb;x0-=4377;x1-=4377;y0-=2777;y1-=2777;sl=np.s_[y0:y1,x0:x1];w=x1-x0;h=y1-y0;k=min(6,900//w)
 tiles=[]
 for name,a in [('V61',native),('Lunar mask restored',restore),('Interiors RGB',s),('User lunar mask',np.repeat(lm[...,None],3,2)),('Original lunar mask',np.repeat(old[...,None],3,2)),('User interiors mask',np.repeat(sm[...,None],3,2))]:
  q=cv(a[sl]).resize((w*k,h*k),Image.Resampling.NEAREST);t=Image.new('RGB',(w*k,h*k+25),'#222222');t.paste(q,(0,25));ImageDraw.Draw(t).text((5,5),name,fill='white');tiles.append(t)
 out=Image.new('RGB',(3*w*k,2*(h*k+25)));[out.paste(t,((j%3)*w*k,(j//3)*(h*k+25))) for j,t in enumerate(tiles)];out.save(O/'vistes'/f'A3_{n}.png')
panel('top',(5250,3303,5305,3350));panel('west',(4870,3720,4970,3950));panel('lower',(5250,4200,5320,4235))
rows=[]
for m in json.loads((O/'A2_marks.json').read_text()):
 x0,y0,x1,y1=m['bbox'];sl=np.s_[y0-2777:y1-2777,x0-4377:x1-4377];rows.append(dict(**m,lunar_mask_changed=int(np.count_nonzero(lm[sl]!=old[sl])),max_lunar_mask_delta=float(abs(lm[sl]-old[sl]).max()),interiors_mask_max=float(sm[sl].max())))
(O/'A3_mask_diagnosis.json').write_text(json.dumps(dict(composition_max_DN16=float(error),marks=rows,total_lunar_mask_edits=int(np.count_nonzero(lm!=old)),decreases=int(np.count_nonzero(lm<old)),increases=int(np.count_nonzero(lm>old))),indent=2));np.save(A/'A3_restored_lunar_mask_preview.npy',restore)
