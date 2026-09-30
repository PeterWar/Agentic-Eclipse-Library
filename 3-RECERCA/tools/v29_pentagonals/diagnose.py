"""Read-only V29 inputs; diagnostic previews, never masks for deletion."""
from pathlib import Path
import json, hashlib
import numpy as np
import cv2
from PIL import Image, ImageDraw

ROOT=Path('/Users/USUARI/Downloads/Eclipse 2026')
C=ROOT/'research/tools/v29/cau_final'
OUT=Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v29_pentagonals_20260905')
HERE=Path(__file__).parent
Image.MAX_IMAGE_PIXELS=None
cx,cy=5361.768112,3775.747534
rs=440.603048830
def load(n):return np.load(C/(n+'.npy'),mmap_mode='r')
def view(a,fn):
    a=np.asarray(a)
    im=Image.fromarray(np.uint8(np.clip(a,0,1)*255))
    im.thumbnail((1800,1800),Image.Resampling.LANCZOS);im.save(OUT/fn)
def panel(arrays,names,fn,size=800):
    canvas=Image.new('RGB',(size*len(arrays),size+35),'#181818');draw=ImageDraw.Draw(canvas)
    for i,(a,name) in enumerate(zip(arrays,names)):
        im=Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('RGB');im=im.resize((size,size),Image.Resampling.LANCZOS)
        canvas.paste(im,(i*size,35));draw.text((i*size+8,10),name,fill='white')
    canvas.save(OUT/fn)

def main():
    tif=Path('/Users/USUARI/Downloads/pentagonals.tif')
    rgb=np.asarray(Image.open(tif).convert('RGB'))
    blue=(rgb[...,2].astype(int)>rgb[...,0].astype(int)+30)&(rgb[...,2].astype(int)>rgb[...,1].astype(int)+20)
    n,lab,stats,centres=cv2.connectedComponentsWithStats(blue.astype('uint8'),8)
    components=[{'bbox':list(map(int,stats[i,:4])),'pixels':int(stats[i,4]),'xy':centres[i].tolist()} for i in range(1,n) if stats[i,4]>30]
    final=load('gran_final');gray=rgb[...,0].astype(np.float32)/255
    valid=load('gran_support');samp=valid[::7,::7]&~blue[::7,::7]
    aa=gray[::7,::7][samp].astype(float);bb=final[::7,::7][samp].astype(float)
    fit=np.polyfit(bb,aa,1)
    rep={'input':str(tif),'sha256':hashlib.sha256(tif.read_bytes()).hexdigest(),'shape':list(rgb.shape),'marks':components,'tif_vs_gran':{'pearson':float(np.corrcoef(aa,bb)[0,1]),'affine':fit.tolist(),'rmse':float(np.sqrt(np.mean((aa-bb)**2)))}}
    ys=slice(2350,5200);xs=slice(3935,6785);roi=(ys,xs)
    panel([rgb[roi]/255,final[roi]],['Pere: marques','V29: capa 03 original'],'DIAG_01_marques_original.png')
    raw=load('gran_raw');sm=load('gran_smoothed')
    scale=json.loads((C/'gran_azimuthal_receipt.json').read_text())['scale_tanh']
    panel([.5+.5*np.tanh(raw[roi]/scale),.5+sm[roi],final[roi]],['Abans suavitzat i H1','Despres suavitzat, abans H1','Despres H1: lliurada'],'DIAG_02_etapes.png')
    av=load('angular_vixen_raw');ass=load('angular_sony_raw')
    v=load('vixen_total')[...,1];s=load('sony_corrected_total')[...,1]
    panel([.5+.5*np.tanh(av[roi]/.03),.5+.5*np.tanh(ass[roi]/.03)],['Angular Vixen cru, escala comuna','Angular Sony cru, escala comuna'],'DIAG_03_trens_crus.png')
    yy,xx=np.ogrid[ys,xs];r=np.hypot(xx-cx,yy-cy)
    norm=[]
    for a in [v[roi],s[roi]]:
        lx=np.log(np.maximum(a,1e-8));bins=np.floor(r/8).astype(int)
        med=np.zeros(bins.max()+1)
        for i in np.unique(bins):med[i]=np.median(lx[bins==i])
        norm.append(.5+(lx-med[bins])*.8)
    panel(norm,['Font Vixen: ln I, perfil retirat nomes per veure','Font Sony: ln I, perfil retirat nomes per veure'],'DIAG_04_fonts.png')
    view(final,'DIAG_05_capa03_llenc_sencer.png')
    (HERE/'diagnostic_receipt.json').write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps(rep))
if __name__=='__main__':main()
