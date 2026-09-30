"""A8: compost acumulat capa a capa (de baix a dalt) als sectors marcats: índex de vora (pic 452–456 / mitjana 462–468 − 1) i panells visuals."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.ndimage import map_coordinates
from PIL import Image, ImageDraw, ImageFont, ImageCms
CX,CY=5377-4377-1.6,3777-2777-0.9; RR=np.arange(440,480,0.25)
def perfil(img,az0,az1):
    th=np.deg2rad(np.arange(az0,az1,0.25)); xs=CX+RR[None,:]*np.cos(th[:,None]); ys=CY-RR[None,:]*np.sin(th[:,None])
    return np.median(map_coordinates(img,[ys.ravel(),xs.ravel()],order=1,mode='nearest').reshape(len(th),len(RR)),0)
sectors={'m1 dalt':(76,100),'m2 NW':(148,158),'m3-4 W':(163,173),'m5 Weq':(177,181),'m6 WSW':(189,199),'m8 SSW':(240,254),'ctrl E':(-10,10),'ctrl S':(260,280),'ctrl NE':(40,60)}
Cb,ab,passos=recompon(retorna_passos=True)
ordre=[l['id'] for l in IDX['layers'] if l['visible'] and l['id']!=218]
print('índex de vora = L(pic 452–456)/L(462–468) − 1, del compost acumulat després d\'afegir cada capa (files) per sector (columnes)')
print('capa'.ljust(34)+''.join(f'{k:>9s}' for k in sectors))
prev={k:None for k in sectors}
for lid in ordre:
    C,a=passos[lid]; L=C.mean(-1); row=f"{lid:>3} {LAYERS[lid]['name'][:28]:28s} "
    for k,(a0,a1) in sectors.items():
        p=perfil(L,a0,a1); pic=p[(RR>=452)&(RR<=456)].max(); ext=p[(RR>=462)&(RR<=468)].mean(); row+=f'{pic/ext-1:+9.3f}'
    print(row)
# panells visuals: seqüència acumulada per marca (finestres 240 px, ×3), estirament comú per marca
src=ImageCms.ImageCmsProfile(SP+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
marques=json.load(open(SP+'/a1_marques.json'))
etapes=[(3,'base'),(42,'+NRGF'),(53,'+ACHF'),(46,'+RHEF loc'),(56,'+WOW'),(30,'+earthshine'),(76,'+interiors'),(96,'+perles96'),(204,'+perles204'),(202,'+estrelles')]
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',16)
except Exception: f=ImageFont.load_default()
S=200; Z=3
for q in marques:
    if q['id']==7: continue
    cx,cy=q['centre']; ax=int(np.clip(cx-4377-S//2,0,2000-S)); ay=int(np.clip(cy-2777-S//2,0,2000-S))
    pan=Image.new('RGB',(len(etapes)*(S*Z+8)+8,S*Z+40),(20,20,22)); d=ImageDraw.Draw(pan)
    for j,(lid,nom) in enumerate(etapes):
        C,a=passos[lid]; crop=C[ay:ay+S,ax:ax+S]*a[ay:ay+S,ax:ax+S,None]  # sobre negre
        im=srgb(crop).resize((S*Z,S*Z),Image.Resampling.NEAREST); pan.paste(im,(8+j*(S*Z+8),8)); d.text((8+j*(S*Z+8),S*Z+14),f'{nom} (id {lid})',fill=(230,230,225),font=f)
    pan.save(SP+f"/v_A8_cumulatiu_marca{q['id']}.png")
print('panells fets')
