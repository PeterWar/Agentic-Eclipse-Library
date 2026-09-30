from pathlib import Path
import json,cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[3];O=R/'4-RESULTATS/v112_20260928';rep=json.loads((O/'ASTROMETRIA.json').read_text());old=json.loads((R/rep['Brno']['old_registration']).read_text())['imatges'];cat=json.loads((R/rep['catalogue']).read_text())['stars'];scale=1200/10551;h=round(7506*scale)
canvas=Image.new('RGB',(2400,(h+80)*3),(18,22,28));d=ImageDraw.Draw(canvas)
try:font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',22)
except:font=ImageFont.load_default()
for row,key in enumerate(['200','400','530']):
 spec=rep['Brno']['references'][key];path=R/rep['Brno']['originals']/spec['source'];rgb=cv2.imread(str(path),cv2.IMREAD_UNCHANGED)
 if rgb.ndim==2:rgb=np.repeat(rgb[...,None],3,axis=2)
 rgb=rgb[...,:3][...,::-1]
 if rgb.dtype==np.uint16:rgb=np.round(rgb.astype(float)/257).astype('uint8')
 aold=np.array(old[spec['source']]['optim' if key=='530' else 'optim3']['A_png_a_v']);anew=np.array(spec['new_A'])
 for col,(name,A) in enumerate([('Registre coronal conservat',aold),('Alineacio estel·lar separada',anew)]):
  img=cv2.warpAffine(rgb,A*scale,(1200,h),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);im=Image.fromarray(img);dd=ImageDraw.Draw(im)
  for idx,s in enumerate(cat):
   x,y=s['x']*scale,s['y']*scale
   if 0<=x<1200 and 0<=y<h:
    dd.line((x-4,y,x+4,y),fill=(50,210,255));dd.line((x,y-4,x,y+4),fill=(50,210,255))
  y=row*(h+80);canvas.paste(im,(col*1200,y+70));d.text((col*1200+20,y+10),f'Brno {key} mm · {name}',fill='white',font=font);d.text((col*1200+20,y+38),'Creus: centres RAW transportats de la capa 202',fill=(70,220,255),font=font)
canvas.save(O/'ASTROMETRIA_REFERENCIES.png')
print('ASTROMETRIA_REFERENCIES.png')
