from pathlib import Path
import sys,json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];O=R/'4-RESULTATS/v112_20260928'
sys.path.insert(0,str(R/'3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB
f=json.loads((O/'FONT.json').read_text());p=PSB(str(R/f['source']))
comp=p.composite()[...,:3];np.save(O/'V111_compost_desat.npy',comp)
im=Image.fromarray((comp/257).astype(np.uint8));im.resize((2400,1707)).save(O/'V111_amb_marques.png')
alpha,org=p.channel(412,-1);rgb=np.stack([p.channel(412,c)[0] for c in range(3)],-1)
np.savez_compressed(O/'marques412.npz',alpha=alpha,rgb=rgb,origin=org)
labels,n=ndi.label(alpha>0);items=[]
canvas=im.resize((2400,1707));draw=ImageDraw.Draw(canvas);scale=2400/p.width
for i,sl in enumerate(ndi.find_objects(labels),1):
 if sl is None:continue
 yy,xx=sl;m=labels[sl]==i;vals=rgb[sl][m];colour=np.median(vals,axis=0).astype(int).tolist()
 box=[xx.start+org[0],yy.start+org[1],xx.stop+org[0],yy.stop+org[1]]
 items.append(dict(id=i,box=box,pixels=int(m.sum()),RGB_median=colour,alpha_max=int(alpha[sl][m].max()),alpha_median=float(np.median(alpha[sl][m]))))
 b=[int(v*scale) for v in box];cc=(255,0,255) if colour[0]>50000 else (0,255,255)
 draw.rectangle(b,outline=cc,width=2);draw.text((b[0]+4,b[1]+4),str(i),fill=cc)
canvas.save(O/'MAPA_MARQUES.png');(O/'MARQUES.json').write_text(json.dumps(items,indent=2)+'\n')
manual={}
for lid in [234,308]:
 a=p.channel_box(lid,-2,(0,0,p.width,p.height));np.save(O/f'L{lid}_mascara.npy',a)
 y,x=np.nonzero(a>0);manual[str(lid)]=dict(nonzero=int(len(x)),range=[int(a.min()),int(a.max())],box=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)],opacity=p.layer(lid)['opacity'])
 z=Image.fromarray((a/257).astype(np.uint8));z.resize((2400,1707)).save(O/f'L{lid}_mascara.png')
(O/'MANUAL.json').write_text(json.dumps(manual,indent=2)+'\n');print(json.dumps(items,indent=2));print(manual)
