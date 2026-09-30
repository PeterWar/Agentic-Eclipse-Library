"""c4 (V105) · Làmines 4:1 del compost EMULAT (sense les capes d'ajust de Pere): 09 | V104 | V105. Ús: c4_laminas_emulades.py <carpeta amb COMP_V10x_emul.npy> <etiqueta>"""
import sys, numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
folder=Path(sys.argv[1]); tag=sys.argv[2]
bx0,by0=4677,3077
V4=np.load(folder/'COMP_V104_emul.npy'); V5=np.load(folder/'COMP_V105_emul.npy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v73_marques_v71_20260917')); from psb69 import PSB
_p=PSB(str(Path(__file__).resolve().parents[3]/'1-PHOTOSHOP/V104.psb')); r3=np.zeros((1400,1400,3),np.float32)
for c in range(3):
    ch,(ox,oy)=_p.channel(303,c); r3[...,c]=ch[by0-oy:by0-oy+1400,bx0-ox:bx0-ox+1400]/65535
coords={'dalt':(5246,3283,5506,3413),'dalt_esquerra':(4986,3386,5126,3526),'esquerra':(4853,3706,4993,3846),'baix_esquerra':(4986,4026,5126,4166),'baix':(5246,4189,5506,4319),'dreta':(5759,3706,5899,3846)}
for nm,(a,b,c,d) in coords.items():
    ims=[]
    for t,arr in [('09 1/60 x2 (Pere)',r3),('V104 (emulada, sense ajustos)',V4),('V105 (emulada, sense ajustos)',V5)]:
        cr=arr[b-by0:d-by0,a-bx0:c-bx0]; im=Image.fromarray(np.uint8(np.clip(cr,0,1)*255)).resize(((c-a)*4,(d-b)*4),Image.NEAREST)
        cv=Image.new('RGB',(im.width,im.height+22),'#202020'); cv.paste(im,(0,22)); ImageDraw.Draw(cv).text((6,5),t,fill='white'); ims.append(cv)
    out=Image.new('RGB',(sum(i.width for i in ims)+12,ims[0].height),'white'); x=0
    for i in ims: out.paste(i,(x,0)); x+=i.width+6
    out.save(folder/f'COMP4_{tag}_{nm}.png')
print('ok')
