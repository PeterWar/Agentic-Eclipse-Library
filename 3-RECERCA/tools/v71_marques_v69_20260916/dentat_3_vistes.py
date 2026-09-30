"""dentat_3: vistes ×8 (NEAREST, sRGB via AdobeRGB.icc, sobre blanc) de 6 finestres 80×80 a la vora: V69 | V70 | variant c | variant e | alfa30 V69 | alfa30 V70; fila 2 = mateixes finestres amb estirament p1–p99 (mapa comú de V69)."""
import sys, numpy as np
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
sys.path.insert(0,SP); import compo; from compo import recompon
from PIL import Image, ImageCms, ImageDraw, ImageFont
CX,CY,RS=998.88,998.41,456.0
D=np.load(SP+'/dentat_comps.npz'); f=lambda k: D[k].astype(np.float32)/65535
C69,a69,Cc,ac=f('C69'),f('a69'),f('Cc'),f('ac')
R70=np.load(SP+'/roi_compost_v70.npz'); C70=R70['C'].astype(np.float32)/65535; a70=R70['a'].astype(np.float32)/65535
for lid in (47,49,51,53,55,56,41,42,45,46,30,3,76): compo.OVERRIDE[lid]=SP+f'/roi_L{lid}_v70.npz'
Ce,ae=recompon(); compo.OVERRIDE.clear()
d69=np.load(SP+'/roi_L30.npz'); d70=np.load(SP+'/roi_L30_v70.npz'); A=d69['c-1'].astype(np.float32)/65535
E69=A*d69['c-2'].astype(np.float32)/65535; E70=A*d70['c-2'].astype(np.float32)/65535
src=ImageCms.ImageCmsProfile(SP+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
def blanc(C,a,sl): return C[sl]*a[sl][...,None]+(1-a[sl][...,None])
try: fnt=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',20)
except Exception: fnt=ImageFont.load_default()
S=80; Z=8; noms=['V69','V70','variant c (+30)','variant e (=V70)','alfa capa 30 V69','alfa capa 30 V70']; fitxers=[]
for azd in (90,150,170,190,250,300):
    th=np.deg2rad(azd); cx=CX+454.5*np.cos(th); cy=CY-454.5*np.sin(th); x0=int(round(cx-S/2)); y0=int(round(cy-S/2)); sl=(slice(y0,y0+S),slice(x0,x0+S))
    cols=[blanc(C69,a69,sl),blanc(C70,a70,sl),blanc(Cc,ac,sl),blanc(Ce,ae,sl)]
    lo,hi=np.percentile(cols[0],1),np.percentile(cols[0],99)
    pan=Image.new('RGB',(6*(S*Z+10)+10,2*(S*Z+34)+10),(20,20,22)); dr=ImageDraw.Draw(pan)
    for k,c in enumerate(cols):
        pan.paste(srgb(c).resize((S*Z,S*Z),Image.Resampling.NEAREST),(10+k*(S*Z+10),34))
        pan.paste(srgb(np.clip((c-lo)/(hi-lo+1e-6),0,1)).resize((S*Z,S*Z),Image.Resampling.NEAREST),(10+k*(S*Z+10),34+S*Z+34))
    for k,E in enumerate((E69,E70)):
        im=Image.fromarray(np.uint8(np.clip(E[sl],0,1)*255+.5)).convert('RGB').resize((S*Z,S*Z),Image.Resampling.NEAREST); pan.paste(im,(10+(4+k)*(S*Z+10),34))
        e=E[sl]; im2=Image.fromarray(np.uint8(np.clip((e-0.5)*4+0.5,0,1)*255+.5)).convert('RGB').resize((S*Z,S*Z),Image.Resampling.NEAREST); pan.paste(im2,(10+(4+k)*(S*Z+10),34+S*Z+34))
    for k,n in enumerate(noms): dr.text((10+k*(S*Z+10),8),n,fill=(230,230,225),font=fnt)
    dr.text((10,34+S*Z+8),f'az {azd}° · finestra {S}×{S} px a ({x0+4377},{y0+2777}) del llenç, centre a r=454,5 · fila 2: estirament p1–p99 de V69 (compostos) / (alfa−0,5)×4+0,5 (alfes)',fill=(230,230,225),font=fnt)
    nom=SP+f'/dentat_vistes_az{azd:03d}.png'; pan.save(nom); fitxers.append(nom); print(nom)
