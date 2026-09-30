"""Three independent parameter variants of Pere's preferred ACHF01.

Same source, channel median, S/N map and physical support. Original V29
layers are never modified. No variant is initially stacked by default.
"""
import os,sys,json
from pathlib import Path
os.environ['V29_FINAL_GRID']='1'
D=Path(__file__).parent;ROOT=D.parents[2]
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from common import *
from fuse_and_filter import sn_smooth,centre_rings
from qa_rasters import h1,h1_setup
from audit_geometry import polar,correlate
from PIL import Image
OUT=Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v30_20260905')
CONFIG={'micro1_16':{'name':'04 ACHF micro 1-16 · V30','sigmas':[1,2,4,8,16]},'fi2_48':{'name':'05 ACHF fi 2-48 · V30','sigmas':[2,4,8,16,32,48]},'estructura4_64':{'name':'06 ACHF estructura 4-64 · V30','sigmas':[4,8,16,32,64]}}

def main():
    r,t=coords();m=np.load(CAU/'fusion_support.npy');total=np.load(CAU/'fusion_total.npy',mmap_mode='r');profiles=json.loads((CAU/'refined_detail_receipt.json').read_text())['profiles']
    all_sigmas=sorted({s for v in CONFIG.values() for s in v['sigmas']});rep={'source':'V29 fusion_total unchanged; same radial contrast profiles, medianRGB and S/N map','variants':{}}
    for c in range(3):
        good=m&(total[...,c]>0);x=np.log(np.maximum(total[...,c],1e-8));w=good.astype('float32');p=profiles[str(c)];scale=np.interp(np.log(np.maximum(r/RS,1e-5)),p['lnr_centres'],p['robust_contrast']).astype('float32')
        outs={key:np.zeros((H,W),'float32') for key in CONFIG}
        for s in all_sigmas:
            band=x-normgauss(x,w,s)
            for key,v in CONFIG.items():
                if s in v['sigmas']:outs[key]+=band/len(v['sigmas'])
            log(f'variants channel{c} sigma{s}')
        for key,a in outs.items():np.save(D/f'cau/{key}_c{c}.npy',np.where(good,a/scale,np.nan).astype('float32'))
        del outs,x,good,w,band,scale
    distance=cv2.distanceTransform((m|(r<1.2*RS)).astype('uint8'),cv2.DIST_L2,5);ctx=h1_setup(r,m);rs=np.linspace(1.12,2.5,60).astype('float32');R=polar(np.log(np.maximum(total[...,1],1)),CX,CY,RS,rs)
    for key,v in CONFIG.items():
        reals=[np.load(D/f'cau/{key}_c{c}.npy',mmap_mode='r') for c in range(3)];d=np.zeros((H,W),'float32')
        for y in range(0,H,256):d[y:y+256]=np.nan_to_num(np.nanmedian(np.stack([q[y:y+256] for q in reals]),axis=0),nan=0)
        scale=float(np.percentile(np.abs(d[m]),99))/1.5;sm,_=sn_smooth(.5*np.tanh(d/max(scale,1e-6)),m);centered,hist=centre_rings(sm,m,r);a=np.clip(.5+centered,0,1);a[~m]=.5;u=np.round(a*65535).astype('uint16')
        mask=m*smooth(distance,0,3*max(v['sigmas']));mask=np.round(mask*65535).astype('uint16')
        np.save(D/f'cau/{key}_raw.npy',d);np.save(D/f'cau/{key}_u16.npy',u);np.save(D/f'cau/{key}_mask_u16.npy',mask)
        im=Image.fromarray(np.uint8(u/257));im.thumbnail((1800,1800),Image.Resampling.LANCZOS);im.save(OUT/f'VARIANT_{key}_llenc_sencer.png')
        rep['variants'][key]={**v,'scale_tanh':scale,'H1':h1(a,m,ctx),'H1_history':hist,'geometry':correlate(polar(a,CX,CY,RS,rs),R),'opacity_u8':36,'visible':False,'outer_kernel_taper_px':3*max(v['sigmas']),'support_pixels':int(m.sum()),'inside1_05R_support':int((m&(r<1.05*RS)).sum())}
        log('variant ready '+key)
    savejson(D/'cau/fine_variants_receipt.json',rep)
if __name__=='__main__':main()
