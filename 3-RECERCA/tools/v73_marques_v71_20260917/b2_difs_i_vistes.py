"""B2: (a) magnitud de les diferències de Pere respecte de la meva V71 (quantització de Photoshop o edició real); (b) vistes de les dues capes de marques sobre el compost de Pere i sobre el compost SENSE filtres (part linealitzada) amb estirament."""
import sys, json, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
sys.path.insert(0,NEW)
import compo71; from compo71 import *
from PIL import Image, ImageCms, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter
ROI=(4377,2777,6377,4777); x0,y0,x1,y1=ROI
fonts={3:('c-2',OLD+'/roi_L3_v71.npz'),30:('c0',OLD+'/roi_L30_v71.npz'),41:('c-2',OLD+'/roi_L41_v70.npz'),47:('c0',OLD+'/roi_L47_v70.npz'),51:('c0',OLD+'/roi_L51_v70.npz'),56:('c0',OLD+'/roi_L56_v70.npz'),55:('c0',OLD+'/roi_L55_v70.npz')}
print('(a) diferències Pere vs la meva V71 (ROI):')
for lid,(ch,f) in fonts.items():
    a=np.load(NEW+f'/roi71_L{lid}.npz')[ch].astype(int); b=np.load(f)[ch].astype(int); d=np.abs(a-b)
    print(f'  capa {lid} {ch}: màx {d.max()} DN16 · >2: {int((d>2).sum())} px · >16: {int((d>16).sum())} px · mitjana {d.mean():.2f}')
a=np.load(NEW+'/roi71_L56.npz'); b69=np.load(OLD+'/roi_L56.npz'); d=np.abs(a['c-2'].astype(int)-b69['c-2'].astype(int)); print('  capa 56 màscara vs V69: màx',d.max(),'px>2:',int((d>2).sum()),'· mitjana màscara V69 %.3f → Pere %.3f'%(b69['c-2'].mean()/65535,a['c-2'].mean()/65535))
# (b) compost de Pere (desat) i compost sense filtres (recomposició) 
C=np.load(NEW+'/roi71_compost.npz')['C'].astype(np.float32)/65535
compo71.OVERRIDE.clear(); Cs,as_=recompon(exclou=(219,220,41,42,47,49,51,53,45,46,55,56))   # sense filtres, sense marques
Cf,af=recompon(exclou=(219,220))
np.savez_compressed(NEW+'/roi71_recomp_sensefiltres.npz',C=(np.clip(Cs,0,1)*65535+.5).astype(np.uint16),a=(np.clip(as_,0,1)*65535+.5).astype(np.uint16)); np.savez_compressed(NEW+'/roi71_recomp.npz',C=(np.clip(Cf,0,1)*65535+.5).astype(np.uint16),a=(np.clip(af,0,1)*65535+.5).astype(np.uint16))
# des-fusió de les marques del compost desat: marques 219 i 220 damunt (NORMAL)
def marca(lid):
    m=np.load(NEW+f'/marques_{lid}.npz'); A=np.zeros((2000,2000),np.float32); RGB=np.zeros((2000,2000,3),np.float32); mx,my=int(m['x0'])-x0,int(m['y0'])-y0
    A[my:my+m['A'].shape[0],mx:mx+m['A'].shape[1]]=m['A']/65535; RGB[my:my+m['A'].shape[0],mx:mx+m['A'].shape[1]]=np.dstack([m['R'],m['G'],m['B']])/65535; return A,RGB
A219,M219=marca(219); A220,M220=marca(220)
print('compost desat vs recomposició (sobre blanc, sense marques): |dif| màx %.1f DN16 (fora de les marques)'%((np.abs((Cf*af[...,None]+(1-af[...,None]))-C[...,:3])[(A219==0)&(A220==0)]).max()*65535))
src=ImageCms.ImageCmsProfile(NEW+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
marks=json.load(open(NEW+'/b1_marques.json'))
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',26)
except Exception: f=ImageFont.load_default()
# 1) compost desat (amb marques) + requadres
im=srgb(C[...,:3]); d=ImageDraw.Draw(im)
for lid,col in ((219,(0,255,255)),(220,(255,0,255))):
    for r in marks[str(lid)]:
        bx0,by0,bx1,by1=r['bbox']; d.rectangle([bx0-x0-6,by0-y0-6,bx1-x0+6,by1-y0+6],outline=col,width=2); d.text((bx0-x0-6,by0-y0-34),f"{lid}.{r['id']}",fill=col,font=f)
im.save(NEW+'/v_B2_roi_marques.png')
# 2) la capa 220 sola (alfa ×4) i sobre el compost sense filtres
Image.fromarray(np.uint8(np.clip(A220*4,0,1)*255)).save(NEW+'/v_B2_capa220_alfa.png')
sb=lambda Cc,a: Cc*a[...,None]+(1-a[...,None])
base=sb(Cs,as_); imb=srgb(base); d=ImageDraw.Draw(imb); yy,xx=np.nonzero(A220>0.02)
for yq,xq in zip(yy[::3],xx[::3]): d.point((xq,yq),fill=(255,0,255))
imb.save(NEW+'/v_B2_sensefiltres_marques220.png')
# 3) estirament fort del compost sense filtres: lluminància local (passa-alt σ 3–40) i CROMA (a*,b* aprox: R−G, B−G normalitzats) per veure «verdosos»
L=base.mean(-1); hp=gaussian_filter(L,2)-gaussian_filter(L,40); s=np.std(hp[(np.hypot(*np.mgrid[0:2000,0:2000][::-1]-np.array([[[998.88]],[[998.41]]]))>470)]); v=np.clip(0.5+hp/(5*s),0,1)
Image.fromarray(np.uint8(v*255)).save(NEW+'/v_B2_sensefiltres_passaalt.png')
G=base[...,1]; Rr=base[...,0]; B=base[...,2]; verd=G/np.maximum((Rr+B)/2,1e-4); verd_hp=gaussian_filter(verd,2)-gaussian_filter(verd,40); sv=np.std(verd_hp[np.isfinite(verd_hp)]); vv=np.clip(0.5+verd_hp/(5*sv),0,1)
im=Image.fromarray(np.uint8(vv*255)).convert('RGB'); d=ImageDraw.Draw(im)
for yq,xq in zip(yy[::3],xx[::3]): d.point((xq,yq),fill=(255,0,255))
im.save(NEW+'/v_B2_sensefiltres_verd_hp.png'); print('vistes fetes')
