"""A16c: REVERTEIX el guany a la base (a18: el 'clot' era la banda vermella de la cromosfera, no un dèficit) i deixa només la màscara de cobertura; recompon la ROI V70 i fa el panell abans/després."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
import compo; from compo import *
from PIL import Image, ImageDraw, ImageFont, ImageCms
d3=np.load(SP+'/roi_L3.npz'); v70=np.load(SP+'/roi_L3_v70.npz')
out={k:d3[k] for k in d3.files}; out['c-2']=v70['c-2']; np.savez_compressed(SP+'/roi_L3_v70.npz',**out)
chk=np.load(SP+'/roi_L3_v70.npz'); print('base V70: RGB idèntic a V69:',all(np.array_equal(chk[c],d3[c]) for c in ('c0','c1','c2')),'· màscara canviada en',int((chk['c-2']!=d3['c-2']).sum()),'px')
import os; os.remove(SP+'/guany_base.npy') if os.path.exists(SP+'/guany_base.npy') else None
def compon(v70):
    compo.OVERRIDE.clear()
    if v70:
        for lid in (47,49,51,53,55,56,30,3,41,42,45,46): compo.OVERRIDE[lid]=SP+f'/roi_L{lid}_v70.npz'
    return recompon()
Cb,ab=compon(False); Ca,aa=compon(True)
print('transparència (alfa<0,998) ROI: abans %d → després %d; alfa mín %.4f → %.4f'%(int((ab<0.998).sum()),int((aa<0.998).sum()),ab.min(),aa.min()))
np.savez_compressed(SP+'/roi_compost_v70.npz',C=(np.clip(Ca,0,1)*65535+.5).astype(np.uint16),a=(np.clip(aa,0,1)*65535+.5).astype(np.uint16))
src=ImageCms.ImageCmsProfile(SP+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
marques=json.load(open(SP+'/a1_marques.json'))
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18)
except Exception: f=ImageFont.load_default()
S=180; Z=3; pan=Image.new('RGB',(3*(S*Z+8)+8,7*(S*Z+30)+8),(20,20,22)); d=ImageDraw.Draw(pan); j=0
for q in marques:
    if q['id']==7: continue
    cx,cy=q['centre']; ax=int(np.clip(cx-4377-S//2,0,2000-S)); ay=int(np.clip(cy-2777-S//2,0,2000-S))
    for k,(C,a) in enumerate([(Cb,ab),(Ca,aa)]):
        crop=C[ay:ay+S,ax:ax+S]*a[ay:ay+S,ax:ax+S,None]+(1-a[ay:ay+S,ax:ax+S,None]); pan.paste(srgb(crop).resize((S*Z,S*Z),Image.Resampling.NEAREST),(8+k*(S*Z+8),8+j*(S*Z+30)))
    u=Ca[ay:ay+S,ax:ax+S]; lo,hi=np.percentile(u,2),np.percentile(u,98); pan.paste(srgb(np.clip((u-lo)/(hi-lo+1e-6),0,1)).resize((S*Z,S*Z),Image.Resampling.NEAREST),(8+2*(S*Z+8),8+j*(S*Z+30)))
    d.text((8,8+j*(S*Z+30)+S*Z+6),f"marca {q['id']} · esq: V69 · mig: V70 · dreta: V70 estirat p2–p98",fill=(230,230,225),font=f); j+=1
pan.save(SP+'/v_A16c_abans_despres.png')
# ROI sencera V70 a 1:1 (sobre blanc) i diferència
Image.fromarray(np.uint8(np.clip(np.abs(Ca-Cb).max(-1)*20,0,1)*255)).save(SP+'/v_A16c_diferencia_x20.png'); srgb(Ca*aa[...,None]+(1-aa[...,None])).save(SP+'/v_A16c_roi_v70.png'); print('fet')
