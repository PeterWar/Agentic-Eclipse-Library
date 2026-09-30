"""C3: com ho compara Pere: capa lunar (30) sola, aclarida, V69 | V71 | V72 | LROC (62), a 1:2 i a 1:1 a la regió de la marca; i la relació global de contrast capa~LROC (pendent)."""
import sys, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'; S3='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
from PIL import Image, ImageCms, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter
CX,CY,RS=998.88,998.41,456.0; Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); disc=rr<RS-8
def rgb(path): d=np.load(path); return np.dstack([d['c0'],d['c1'],d['c2']]).astype(np.float32)/65535
C69=rgb(OLD+'/roi_L30.npz'); C71=rgb(OLD+'/roi_L30_v71.npz'); C72=rgb(NEW+'/roi72_L30.npz'); C62=rgb(NEW+'/roi71_L62.npz'); v62=np.load(NEW+'/roi71_L62.npz')['c-1']>30000
src=ImageCms.ImageCmsProfile(NEW+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
# aclarit ×3,5 (com Pere), fons negre fora del disc
k=3.5; x0,y0=int(CX)-500,int(CY)-500
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',22)
except Exception: f=ImageFont.load_default()
ims=[]
for C,nom in ((C69,'V69'),(C71,'V71'),(C72,'V72')):
    A=np.clip(C*k,0,1)*disc[...,None]; ims.append((srgb(A[y0:y0+1000,x0:x0+1000]),nom))
lr=np.clip(C62*(disc&v62)[...,None]*1.0,0,1); ims.append((srgb(lr[y0:y0+1000,x0:x0+1000]),'Compara LROC (62)'))
pan=Image.new('RGB',(4*1010+10,1040),(20,20,22)); d=ImageDraw.Draw(pan)
for j,(im,nom) in enumerate(ims): pan.paste(im,(10+j*1010,10)); d.text((10+j*1010,1012),nom+' · capa sola, ×3,5',fill=(230,230,225),font=f)
pan.resize((pan.width//2,pan.height//2),Image.Resampling.LANCZOS).save(S3+'/v_C3_lluna_x35_v69_v71_v72_lroc.png')
# regió de la marca a 1:1 (400 px)
m7=np.load(NEW+'/marques_219.npz'); Mk=np.zeros((2000,2000),np.float32); mx,my=int(m7['x0'])-4377,int(m7['y0'])-2777; Mk[my:my+m7['A'].shape[0],mx:mx+m7['A'].shape[1]]=m7['A']/65535
R7=np.zeros((2000,2000),bool); R7[3928-2777:4132-2777,5187-4377:5418-4377]=Mk[3928-2777:4132-2777,5187-4377:5418-4377]>0.03
cx,cy=int(np.mean(np.nonzero(R7)[1])),int(np.mean(np.nonzero(R7)[0])); x1,y1=cx-200,cy-200
pan=Image.new('RGB',(4*410+10,440),(20,20,22)); d=ImageDraw.Draw(pan)
for j,(C,nom) in enumerate(((C69,'V69'),(C71,'V71'),(C72,'V72'),(C62,'LROC'))):
    A=np.clip(C*(k if nom!='LROC' else 1.0),0,1)*disc[...,None]; im=srgb(A[y1:y1+400,x1:x1+400]); dd=ImageDraw.Draw(im); yy,xx=np.nonzero(R7[y1:y1+400,x1:x1+400])
    pan.paste(im,(10+j*410,10)); d.text((10+j*410,412),nom,fill=(230,230,225),font=f)
pan.save(S3+'/v_C3_regio_1a1.png')
# pendent global capa~LROC (passa-baix σ12, normalitzat per anells) i a la regió
def ring_norm(A,mask,step=4):
    out=np.full(A.shape,np.nan)
    for kk in range(0,int(RS)+step,step):
        m=mask&(rr>=kk)&(rr<kk+step)
        if m.sum()>10: out[m]=A[m]/np.mean(A[m])-1
    return out
L72=ring_norm(gaussian_filter(C72.mean(-1),12),disc); L62=ring_norm(gaussian_filter(C62.mean(-1),12),disc&v62); L69=ring_norm(gaussian_filter(C69.mean(-1),12),disc)
m=disc&v62&np.isfinite(L72)&np.isfinite(L62)&(rr<RS-40)
for nom,LL in (('V69',L69),('V72',L72)):
    s,b=np.polyfit(L62[m],LL[m],1); print(f'{nom}: capa = {s:.3f} × LROC + {b:.3f} (σ12, anells) · corr {np.corrcoef(L62[m],LL[m])[0,1]:.3f} · a la marca: LROC {L62[R7&m].mean():+.3f} → capa {LL[R7&m].mean():+.3f} (esperat pel pendent {s*L62[R7&m].mean()+b:+.3f})')
print('fet')
