"""B4: panells ×3 a les marques 219.1, 219.4, 219.7, 219.8 i a l'anell 220 a az 30/90/200/300: compost de Pere (des-fusionat) | sense filtres | mapa verd (quocient) | sense filtres estirat."""
import sys, json, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'
sys.path.insert(0,NEW)
from PIL import Image, ImageCms, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter
CX,CY,RS=998.88,998.41,456.0
F=np.load(NEW+'/roi71_recomp.npz'); Cf=F['C'].astype(np.float32)/65535; af=F['a'].astype(np.float32)/65535
S=np.load(NEW+'/roi71_recomp_sensefiltres.npz'); Cs=S['C'].astype(np.float32)/65535; as_=S['a'].astype(np.float32)/65535
src=ImageCms.ImageCmsProfile(NEW+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
sb=lambda C,a: C*a[...,None]+(1-a[...,None])
V=Cs[...,1]/np.maximum((Cs[...,0]+Cs[...,2])/2,1e-4); Vm=np.clip(0.5+(V-np.median(V))*8,0,1)
marks=json.load(open(NEW+'/b1_marques.json'))
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18)
except Exception: f=ImageFont.load_default()
fin=[]
for r in marks['219']:
    if r['id'] in (1,4,7,8): cx,cy=r['centre']; fin.append((f"219.{r['id']}",cx-4377,cy-2777,240 if r['id']==7 else 160))
for a0 in (30,90,200,300): fin.append((f'anell 220 az {a0}',CX+475*np.cos(np.deg2rad(a0)),CY-475*np.sin(np.deg2rad(a0)),160))
Z=3; W=max(w for *_,w in fin); pan=Image.new('RGB',(4*(W*Z+8)+8,len(fin)*(W*Z+30)+8),(20,20,22)); d=ImageDraw.Draw(pan)
for j,(nom,cx,cy,w) in enumerate(fin):
    x0=int(np.clip(cx-w//2,0,2000-w)); y0=int(np.clip(cy-w//2,0,2000-w)); crops=[srgb(sb(Cf,af)[y0:y0+w,x0:x0+w]),srgb(sb(Cs,as_)[y0:y0+w,x0:x0+w]),Image.fromarray(np.uint8(Vm[y0:y0+w,x0:x0+w]*255)).convert('RGB')]
    u=sb(Cs,as_)[y0:y0+w,x0:x0+w]; lo,hi=np.percentile(u,2),np.percentile(u,98); crops.append(srgb(np.clip((u-lo)/(hi-lo+1e-6),0,1)))
    for k,im in enumerate(crops): pan.paste(im.resize((w*Z,w*Z),Image.Resampling.NEAREST),(8+k*(W*Z+8),8+j*(W*Z+30)))
    d.text((8,8+j*(W*Z+30)+w*Z+4),f'{nom} · compost Pere | sense filtres | verd ×8 | sense filtres estirat',fill=(230,230,225),font=f)
pan.save(NEW+'/v_B4_panells.png'); print('fet')
