"""Causal pilots: stop propagating finer neighbouring S/N caps into noisy tiles.

Same original non-azimuthal detail, gain, physical support and H1 method.
No PSB or original cache is modified. Keep the two changes separate.
"""
import os,sys,json
from pathlib import Path
os.environ['V29_FINAL_GRID']='1'
D=Path(__file__).parent;ROOT=D.parents[2]
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from common import *
from fuse_and_filter import sn_smooth,centre_rings
from qa_rasters import h1,h1_setup
from PIL import Image,ImageDraw
OUT=ROOT/'output/v32_20260905'
ROIS={'interior':(5810,3260),'marca_N':(5715,2200),'marca_S':(5130,5160),'exterior':(6500,2520)}
def png(a,p):
    im=Image.fromarray(np.uint8(np.clip(a,0,1)*255));im.thumbnail((1800,1800),Image.Resampling.LANCZOS);im.save(p)
def main():
    rec=json.loads((CAU/'coherent_resolution.json').read_text());grid=np.asarray(rec['grid_sigma'],'float32');n=rec['tile_px'];step=rec['stride_px']
    y,x=np.ogrid[:H,:W];mx=np.broadcast_to((x-n/2)/step,(H,W)).astype('float32');my=np.broadcast_to((y-n/2)/step,(H,W)).astype('float32')
    sig=cv2.remap(grid,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    r,t=coords();sw=smooth(r/RS,2,2.65);sig=(1-sw)*.7+sw*sig
    np.save(D/'cau/local_sigma.npy',sig);png(sig/8,OUT/'SIGMA_local_llenc_sencer.png')
    oldsig=np.load(CAU/'resolution_sigma.npy',mmap_mode='r');m=np.load(CAU/'fusion_support.npy');ctx=h1_setup(r,m)
    d=np.load(CAU/'achf_raw.npy',mmap_mode='r');old=np.load(ROOT/'research/tools/v31/cau/01_final_u16.npy',mmap_mode='r').astype('float32')/65535
    scale=json.loads((CAU/'refined_detail_receipt.json').read_text())['filters']['achf']['scale_tanh']
    candidates={'V31':old};rep={'status':'PILOTS_ONLY','source':'V29 achf_raw, same fixed gain and physical support','map_change':'no minimum erosion; actual512px tile centres and384px stride instead of stretching grid to full canvas','scope':'01 first; azimuthal layers unchanged','cases':{},'sigma_at_rois':{k:{'old':float(oldsig[y,x]),'local':float(sig[y,x])} for k,(x,y) in ROIS.items()}}
    for name,sigma,order in [('baseline_recomputed',oldsig,'after_tanh'),('local_map',sig,'after_tanh'),('old_map_before_tanh',oldsig,'before_tanh'),('local_before_tanh',sig,'before_tanh')]:
        if order=='before_tanh':sm,_=sn_smooth(d,m,sigma=sigma);sm=.5*np.tanh(sm/scale)
        else:sm,_=sn_smooth(.5*np.tanh(d/scale),m,sigma=sigma)
        centered,hist=centre_rings(sm,m,r);a=np.clip(.5+centered,0,1);a[~m]=.5;u=np.round(a*65535).astype('uint16');np.save(D/f'cau/01_{name}_u16.npy',u)
        q={'H1':h1(u.astype('float32')/65535,m,ctx),'H1_history':hist};rep['cases'][name]=q;png(a,OUT/f'PILOT_01_{name}_llenc_sencer.png');candidates[name]=a
        log(name+' H1 '+str(q['H1']['worst']))
    original=np.load(CAU/'achf_u16.npy',mmap_mode='r');recomp=np.load(D/'cau/01_baseline_recomputed_u16.npy',mmap_mode='r');err=np.abs(original.astype('int32')-recomp.astype('int32'));rep['baseline_reproduction']={'max_DN16':int(err.max()),'p99_DN16':float(np.percentile(err,99))}
    png(old,OUT/'V31_01_llenc_sencer.png')
    names=['V31','local_map','old_map_before_tanh','local_before_tanh']
    for roi,(x,y) in ROIS.items():
        panel=Image.new('RGB',(2048,542));draw=ImageDraw.Draw(panel);sl=(slice(y-256,y+256),slice(x-256,x+256))
        for j,name in enumerate(names):
            panel.paste(Image.fromarray(np.uint8(candidates[name][sl]*255)).convert('RGB'),(j*512,30));draw.text((j*512+8,8),name,fill='white')
        panel.save(OUT/f'PILOT_01_{roi}_100.png')
    savejson(D/'sn_pilots.json',rep)
if __name__=='__main__':main()
