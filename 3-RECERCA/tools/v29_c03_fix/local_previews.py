"""Native pixel inspection crops; never modify scientific or PSB dimensions."""
import os,sys,json
from pathlib import Path
os.environ['V29_FINAL_GRID']='1'
D=Path(__file__).parent;ROOT=D.parents[2]
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from common import *
from build_canvas import over
from PIL import Image,ImageDraw
OUT=Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v29_c03_fix_20260905')

def panel(arrays,labels,name):
    h,w=arrays[0].shape[:2];im=Image.new('RGB',(w*len(arrays),h+30));dr=ImageDraw.Draw(im)
    for j,(a,label) in enumerate(zip(arrays,labels)):
        p=Image.fromarray(np.uint8(np.clip(a,0,1)*255));im.paste(p,(j*w,30));dr.text((j*w+8,8),label,fill='white')
    im.save(OUT/name)

def main():
    old=np.load(CAU/'gran_final.npy',mmap_mode='r');new=np.load(D/'gran_u16.npy',mmap_mode='r')
    oldcomp=np.load(CAU/'composite_delivery.npy',mmap_mode='r');newcomp=np.load(D/'composite.npy',mmap_mode='r');mask=np.load(CAU/'gran_mask_final.npy',mmap_mode='r')
    rep={'native_pixel_pilots':[],'full_support_mask_reused':True}
    for name,x,y in [('pentagon_NE',6198,3638),('pentagon_SE',6142,4081),('pentagon_exterior_Sony',6376,4342),('limbe_W',4921,3776),('limbe_N',5362,3335),('limbe_S',5362,4216),('limbe_E',5802,3776)]:
        sl=(slice(y-256,y+256),slice(x-256,x+256));a=old[sl];b=new[sl].astype('float32')/65535
        panel([a,b,.5+(b-a)*2],['03 ABANS ·100%','03 DESPRES ·100%','diferencia x2 ·gris=zero'],f'QA_100_{name}_03.png')
        a=oldcomp[sl];b=newcomp[sl]
        panel([a,b,.5+(b-a)*8],['V29 ABANS ·100%','V29 DESPRES ·100%','diferencia x8 ·gris=zero'],f'QA_100_{name}_V29.png')
        rep['native_pixel_pilots'].append({'name':name,'bbox':[x-256,y-256,x+256,y+256],'display_sampling':'one source pixel per image pixel'})
    # Full-canvas support audit, chunked to keep RAM bounded.
    max_out=0.;count=0
    for y in range(0,H,256):
        sl=slice(y,min(y+256,H));z=mask[sl]==0;diff=np.abs(oldcomp[sl]-newcomp[sl]);max_out=max(max_out,float(np.max(diff[z])) if z.any() else 0);count+=int(z.sum())
    rep['outside03_mask']={'pixels':count,'max_abs_composite_delta':max_out,'PASS':max_out==0};assert max_out==0
    savejson(D/'local_preview_receipt.json',rep)
if __name__=='__main__':main()
