"""Compare positive spatial smoothing of NON-azimuthal detail only.

Exploratory pilots: original gain, support and colors; no circular mask.
No azimuthal layer or original cache is modified.
"""
import os,sys,json
from pathlib import Path
os.environ['V29_FINAL_GRID']='1'
D=Path(__file__).parent;ROOT=D.parents[2]
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from common import *
from PIL import Image,ImageDraw
OUT=Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v31_20260905')
V30=ROOT/'research/tools/v30/cau'
SOURCES={'01':CAU/'achf_u16.npy','02':CAU/'passalt24_u16.npy','04':V30/'micro1_16_u16.npy','05':V30/'fi2_48_u16.npy','06':V30/'estructura4_64_u16.npy'}
ROIS={'interior':(5810,3260),'mitja':(6100,3000),'exterior':(6500,2520),'marques_N':(5715,2200),'marques_S':(5130,5160)}
def png(a,p):
    im=Image.fromarray(np.uint8(np.clip(a,0,1)*255));im.thumbnail((1800,1800),Image.Resampling.LANCZOS);im.save(p)
def main():
    mask=np.load(CAU/'fusion_support.npy');w=mask.astype('float32');receipt={'status':'PILOT_ONLY','operator':'normalized isotropic positive Gaussian on neutral-relative detail, fixed gain','sigma_px':[1.5,3,5],'files':{}}
    den={s:gauss(w,s) for s in (1.5,3.,5.)}
    for tag,path in SOURCES.items():
        a=np.load(path,mmap_mode='r').astype('float32')/65535;panels={n:[a[y-256:y+256,x-256:x+256].copy()] for n,(x,y) in ROIS.items()}
        png(a,OUT/f'PILOT_{tag}_original_llenc_sencer.png')
        for s in (1.5,3.,5.):
            b=.5+gauss((a-.5)*w,s)/np.maximum(den[s],1e-8);b[~mask]=.5
            file=D/f'cau/{tag}_s{s:g}_u16.npy';np.save(file,np.round(np.clip(b,0,1)*65535).astype('uint16'))
            png(b,OUT/f'PILOT_{tag}_s{s:g}_llenc_sencer.png');receipt['files'][f'{tag}_{s:g}']=str(file)
            for n,(x,y) in ROIS.items():panels[n].append(b[y-256:y+256,x-256:x+256].copy())
            log(f'pilot non-azimuthal {tag} sigma{s:g}')
        for n,arr in panels.items():
            im=Image.new('RGB',(2048,542));draw=ImageDraw.Draw(im)
            for j,(a,label) in enumerate(zip(arr,['original','isotropic1.5px','isotropic3px','isotropic5px'])):
                im.paste(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('RGB'),(j*512,30));draw.text((j*512+8,8),tag+' '+label,fill='white')
            im.save(OUT/f'PILOT_{tag}_{n}_100.png')
    savejson(D/'pilot_receipt.json',receipt)
if __name__=='__main__':main()
