"""A17: capa LROC (id 62) i capa lunar (id 30) costat a costat, amb la marca 7 i el mínim trobat als RAW; passa-alt σ40 per veure el patró de mars."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageDraw, ImageFont
CX,CY,RS=998.88,998.41,456.0
m=np.load(SP+'/marques_218.npz'); M=np.zeros((2000,2000),np.float32); mx,my=int(m['x0'])-4377,int(m['y0'])-2777; M[my:my+m['A'].shape[0],mx:mx+m['A'].shape[1]]=m['A']/65535
yy,xx=np.mgrid[0:2000,0:2000]; rp=np.hypot(xx-CX,yy-CY)
pans=[]
for lid,nom in [(30,'capa lunar (id 30) · revelat de Pere'),(62,'Compara LROC (id 62, oculta)')]:
    rgb,a=carrega(lid); L=rgb.mean(-1); d=np.load(SP+f'/roi_L{lid}.npz'); al=d['c-1'].astype(np.float32)/65535
    hp=gaussian_filter(L,3)-gaussian_filter(L,40); k=(rp<0.92*RS)&(al>0.5); s=hp[k].std(); img=np.clip(0.5+hp/(4*s),0,1); img[~k]=0.15
    lin=np.clip((L-np.percentile(L[k],1))/(np.percentile(L[k],99.5)-np.percentile(L[k],1)+1e-9),0,1); lin[~k]=0.15
    for tag,im in [('lineal',lin),('passa-alt σ3–40',img)]:
        S=int(CY)-500,int(CY)+500,int(CX)-500,int(CX)+500; crop=im[S[0]:S[1],S[2]:S[3]]; pil=Image.fromarray(np.uint8(crop*255)).convert('RGB'); dr=ImageDraw.Draw(pil)
        mk=M[S[0]:S[1],S[2]:S[3]]>0.2; ys,xs=np.nonzero(mk)
        for yq,xq in zip(ys[::7],xs[::7]): dr.point((xq,yq),fill=(255,140,0))
        # mínim RAW (−62,+299) i posició esperada (−44,+234) respecte del centre físic
        for (ox,oy,col) in [(-62,299,(0,255,255)),(-44.5,234.5,(0,255,0))]:
            cx,cy=500+ox,500+oy; dr.ellipse([cx-45,cy-45,cx+45,cy+45],outline=col,width=2)
        pans.append((f'{nom} · {tag}',pil))
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18)
except Exception: f=ImageFont.load_default()
pan=Image.new('RGB',(2*1010+10,2*1035+10),(20,20,22)); dr=ImageDraw.Draw(pan)
for j,(nom,pil) in enumerate(pans):
    X=10+(j%2)*1010; Y=10+(j//2)*1035; pan.paste(pil,(X,Y)); dr.text((X,Y+1005),nom+' · taronja: marca 7 · cian: mínim RAW (−62,+299) · verd: centre de la marca',fill=(230,230,225),font=f)
pan.save(SP+'/v_A17_lroc_vs_lluna.png'); print('fet')
