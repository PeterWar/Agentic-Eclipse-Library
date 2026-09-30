"""Assemble default and mutually exclusive comparison views on the same base."""
import os,sys,json
from pathlib import Path
os.environ['V29_FINAL_GRID']='1'
D=Path(__file__).parent;ROOT=D.parents[2]
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from common import *
from build_canvas import over
from PIL import Image,ImageDraw
FIX=ROOT/'research/tools/v29_c03_fix';OUT=Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v30_20260905')

def png(a,name):
    im=Image.fromarray(np.uint8(np.clip(a,0,1)*255));im.thumbnail((1800,1800),Image.Resampling.LANCZOS);im.save(OUT/name)
def panel(arrays,labels,name):
    h,w=arrays[0].shape[:2];im=Image.new('RGB',(len(arrays)*w,h+30));dr=ImageDraw.Draw(im)
    for i,(a,label) in enumerate(zip(arrays,labels)):
        im.paste(Image.fromarray(np.uint8(np.clip(a,0,1)*255)),(i*w,30));dr.text((i*w+8,8),label,fill='white')
    im.save(OUT/name)
def main():
    base=np.load(CAU/'composite_base.npy',mmap_mode='r');fg=np.load(CAU/'foreground_add.npy',mmap_mode='r');old=np.load(FIX/'composite.npy',mmap_mode='r');gmask=np.load(CAU/'gran_mask_final.npy',mmap_mode='r');amask=np.load(CAU/'achf_mask_final.npy',mmap_mode='r');pmask=np.load(CAU/'passalt24_mask_final.npy',mmap_mode='r');achf=np.load(CAU/'achf_final.npy',mmap_mode='r');pal=np.load(CAU/'passalt24_final.npy',mmap_mode='r');vrep=json.loads((D/'cau/fine_variants_receipt.json').read_text());rep={'default':'radial4 + unchanged01/02','alternatives':'one alternative instead of its parent, never automatically stacked','previews':[]}
    outputs={}
    for tag in ['default_r4','suau_r8',*vrep['variants']]:
        s=8 if tag=='suau_r8' else 4;g=np.load(D/f'cau/gran_r{s}_u16.npy',mmap_mode='r').astype('float32')/65535
        comp=over(base,g[...,None],gmask,38/255,'overlay')
        a=np.load(D/f'cau/{tag}_u16.npy',mmap_mode='r').astype('float32')/65535 if tag in vrep['variants'] else achf
        mask=np.load(D/f'cau/{tag}_mask_u16.npy',mmap_mode='r').astype('float32')/65535 if tag in vrep['variants'] else amask
        comp=over(comp,a[...,None],mask,36/255,'overlay');comp=over(comp,pal[...,None],pmask,20/255,'overlay');comp=np.clip(comp+fg,0,1)
        png(comp,f'V30_{tag}_llenc_sencer.png');np.save(D/f'cau/composite_{tag}.npy',comp);outputs[tag]=comp;rep['previews'].append(tag);log('composite '+tag)
    for name,x,y in [('limbe_W',4921,3776),('limbe_N',5362,3335),('limbe_E',5802,3776),('limbe_S',5362,4216),('marca_N',5715,2200),('marca_W',3600,3290),('marca_E',7200,3560),('marca_S',5130,5160),('filaments',5960,3260)]:
        sl=(slice(y-256,y+256),slice(x-256,x+256));a=old[sl];b=outputs['default_r4'][sl];c=outputs['suau_r8'][sl]
        panel([a,b,c,.5+(b-a)*8],['V29','V30 r4','alternativa r8','r4-V29 x8'],f'QA_100_{name}.png')
    for name,x,y in [('interior',5810,3260),('mitja',6100,3000),('exterior',6500,2520)]:
        sl=(slice(y-256,y+256),slice(x-256,x+256));arrays=[achf[sl]]+[np.load(D/f'cau/{tag}_u16.npy',mmap_mode='r')[sl].astype('float32')/65535 for tag in vrep['variants']]
        panel(arrays,['01 V29',*vrep['variants']],f'QA_100_variants_{name}.png')
    maxout=0
    for y in range(0,H,256):
        sl=slice(y,y+256);m=gmask[sl]==0;q=np.abs(old[sl]-outputs['default_r4'][sl]);maxout=max(maxout,float(q[m].max()) if m.any() else 0)
    rep['outside03_mask_max_abs_change']=maxout;assert maxout==0
    savejson(D/'cau/preview_receipt.json',rep)
if __name__=='__main__':main()
