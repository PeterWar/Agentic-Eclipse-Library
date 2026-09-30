import sys,json,hashlib
from pathlib import Path
import numpy as np, tifffile
from PIL import Image,ImageDraw
R=Path('/Users/USUARI/Desktop/Eclipse 2026'); O=Path('/private/tmp/eclipse_v104_diagnosi_20260926')
sys.path.insert(0,str(R/'3-RECERCA/tools/v71_marques_v69_20260916'))
from psb69 import PSB
p=PSB(str(R/'1-PHOTOSHOP/V104.psb')); box=(4600,3000,6150,4550)
(O/'index.json').write_text(json.dumps(p.layers,ensure_ascii=False,indent=2))
# Diagnostic exports only. Original PSB is opened read-only; no Photoshop changes.
full=np.zeros((p.height//8+1,p.width//8+1,3),np.uint16)
for lid in (303,3,258,76,96,41,42,51,55,56):
    data={}
    for c in p.layer(lid)['chans']:
        a,org=p.channel(lid,c)
        if lid==303 and c in (0,1,2):
            # Full canvas view retains the layer's placement, unaltered.
            tmp=np.zeros((p.height,p.width),np.uint16); x,y=org; h,w=a.shape;tmp[y:y+h,x:x+w]=a
            full[:,:,c]=tmp[::8,::8]
        x,y=org;h,w=a.shape;x0,y0,x1,y1=box
        default=p.layer(lid)['mask']['background']*257 if c==-2 else 0
        dst=np.full((y1-y0,x1-x0),default,np.uint16)
        xa,ya=max(x,x0),max(y,y0);xb,yb=min(x+w,x1),min(y+h,y1)
        if xb>xa and yb>ya:dst[ya-y0:yb-y0,xa-x0:xb-x0]=a[ya-y:yb-y,xa-x:xb-x]
        data['c'+str(c)]=dst
    np.savez(O/f'L{lid}.npz',**data); print('extracted',lid,flush=True)
Image.fromarray((full/257).astype(np.uint8)).save(O/'capa09_llenc.png')
ref=np.stack([np.load(O/'L303.npz')['c'+str(c)] for c in range(3)],-1)
comp=tifffile.imread(R/'4-RESULTATS/v103_banda_20260926/E/vistes/V104_lluna.tif')[...,:3]
np.save(O/'v104_natiu_original.npy',comp)
coords={'dalt':(646,283,906,413),'dalt_esquerra':(386,386,526,526),'esquerra':(253,706,393,846),'baix_esquerra':(386,1026,526,1166),'baix':(646,1189,906,1319),'dreta':(1159,706,1299,846)}
for name,(x0,y0,x1,y1) in coords.items():
    ims=[]
    for a,title in ((ref,'Capa 09 1/60 x2 - Pere'),(comp,'V104 - render natiu lliurat')):
        im=Image.fromarray((a[y0:y1,x0:x1]/257).clip(0,255).astype(np.uint8)).resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.NEAREST)
        canvas=Image.new('RGB',(im.width,im.height+32),'#202020');canvas.paste(im,(0,32));ImageDraw.Draw(canvas).text((8,8),title,fill='white');ims.append(canvas)
    out=Image.new('RGB',(ims[0].width+ims[1].width+12,ims[0].height),'white');out.paste(ims[0],(0,0));out.paste(ims[1],(ims[0].width+12,0));out.save(O/f'comparacio_{name}.png')
print('done',flush=True)
