"""C5: la capa lunar amb el terra restat (punt negre al percentil 2 del disc, blanc al 99,5) — el que veuria Pere en pujar el contrast — V69 | V71 | V72 | LROC; i perfil radial de la mitjana per anell (és pla?)."""
import sys, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'; S3='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter
CX,CY,RS=998.88,998.41,456.0; Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); disc=rr<RS-6
def L(path): d=np.load(path); return np.dstack([d['c0'],d['c1'],d['c2']]).astype(np.float32).mean(-1)/65535
L69=L(OLD+'/roi_L30.npz'); L71=L(OLD+'/roi_L30_v71.npz'); L72=L(NEW+'/roi72_L30.npz'); L62=L(NEW+'/roi71_L62.npz'); v62=np.load(NEW+'/roi71_L62.npz')['c-1']>30000
print('mitjana per anell de V72 (r 50…440, pas 50):',[round(float(L72[disc&(rr>=k)&(rr<k+20)].mean()),4) for k in range(50,441,50)])
def stretch(A,mask,lo=2,hi=99.5): a,b=np.percentile(A[mask],lo),np.percentile(A[mask],hi); return np.clip((A-a)/(b-a),0,1)*mask
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',22)
except Exception: f=ImageFont.load_default()
x0,y0=int(CX)-500,int(CY)-500; pan=Image.new('RGB',(4*1010+10,1040),(20,20,22)); d=ImageDraw.Draw(pan)
for j,(A,m,nom) in enumerate(((L69,disc,'V69'),(L71,disc,'V71'),(L72,disc,'V72'),(L62,disc&v62,'Compara LROC'))):
    im=Image.fromarray(np.uint8(stretch(gaussian_filter(A,1.5),m)[y0:y0+1000,x0:x0+1000]*255)).convert('RGB'); pan.paste(im,(10+j*1010,10)); d.text((10+j*1010,1012),nom+' · terra restat (p2→negre, p99,5→blanc)',fill=(230,230,225),font=f)
pan.resize((pan.width//2,pan.height//2),Image.Resampling.LANCZOS).save(S3+'/v_C5_lluna_contrast.png'); print('fet')
