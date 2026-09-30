"""Exact editable-layer previews with physical footprint kernel coverage."""
from common import *
from build_canvas import over,png
from PIL import Image,ImageDraw

def main():
    assert FINAL_GRID
    m=np.load(CAU/'fusion_support.npy');r,_=coords()
    # The lunar hole is ignored ONLY for computing the outer sensor edge.
    # The actual temporal support remains zero inside the occulted union.
    distance=cv2.distanceTransform((m|(r<1.2*RS)).astype(np.uint8),cv2.DIST_L2,5)
    masks={}
    for name,sigma in [('achf',32),('passalt24',24),('gran',128)]:
        support=np.load(CAU/'gran_support.npy') if name=='gran' and (CAU/'gran_support.npy').exists() else m
        al=support*smooth(distance,0,3*sigma)
        masks[name]=np.round(al*65535).astype(np.uint16)/65535
        np.save(CAU/f'{name}_mask_final.npy',masks[name].astype(np.float32))
        a=np.load(CAU/f'{name}_u16.npy').astype(np.float32)/65535
        np.save(CAU/f'{name}_final.npy',a);png(.5+(a-.5)*masks[name],f'FINAL_LAYER_{name}.png')
    b=np.load(CAU/'composite_base.npy');fg=np.load(CAU/'foreground_add.npy',mmap_mode='r')
    candidates=[('suau',.12,.12,.2),('equilibrat',.2,.2,.3),('detall',.3,.3,.4)]
    opacities={'gran':128,'achf':178,'passalt24':102}
    for tag,af,pf,gf in candidates:
        strength={'achf':af,'passalt24':pf,'gran':gf};comp=b.copy();states=[comp]
        for name in ('gran','achf','passalt24'):
            a=np.load(CAU/f'{name}_final.npy',mmap_mode='r')
            raster=np.round(np.clip(.5+(a-.5)*strength[name],0,1)*65535).astype(np.uint16).astype(np.float32)/65535
            comp=over(comp,raster[...,None],masks[name],opacities[name]/255,'overlay')
            if tag=='equilibrat':states.append(comp)
        comp=np.clip(comp+fg,0,1);png(comp,f'CANDIDAT_{tag}_llenc_sencer.png')
        np.save(CAU/f'composite_{tag}.npy',comp)
        cfg={'accepted_for_packaging':False,'candidate':tag,'layers':{name:{'strength':strength[name],'opacity_u8':opacities[name],'outer_kernel_taper_px':3*{'achf':32,'passalt24':24,'gran':128}[name]} for name in strength},'support':'actual observed temporal lunar union; only physical outer footprint kernel tapers'}
        savejson(CAU/f'config_{tag}.json',cfg)
        # 1:1 panels, no resampling, separate sites and cumulative limb states.
        for label,cx,cy,n in [('ghost',4879,2549,512),('arcs_SE',6078,4998,640),('arcs_NE',5743,2374,512),('limb',4900,3776,512),('outer_NW',3700,2400,512)]:
            sl=(slice(cy-n//2,cy+n//2),slice(cx-n//2,cx+n//2))
            Image.fromarray(np.round(comp[sl]*255).astype(np.uint8)).save(OUT/f'1a1_{tag}_{label}.png')
        if tag=='equilibrat':
            n=512;cx,cy=4900,3776;sl=(slice(cy-n//2,cy+n//2),slice(cx-n//2,cx+n//2));panel=Image.new('RGB',(n*4,n+30))
            dr=ImageDraw.Draw(panel)
            for j,state in enumerate(states):
                panel.paste(Image.fromarray(np.round(np.clip(state[sl],0,1)*255).astype(np.uint8)),(j*n,30));dr.text((j*n+10,8),['base','+ ample','+ ACHF fi','+ passa-alt'][j],fill='white')
            panel.save(OUT/'QA_limb_acumulat_1a1.png')
        log('candidate '+tag)
    savejson(CAU/'footprint_taper_receipt.json',{'definition':'smoothstep distance to actual outer coverage; lunar hole filled only for distance calculation; no circular radial fade','kernel_3sigma_px':{'achf':96,'passalt24':72,'gran':384},'all_inner_observed_pixels_full_alpha':{n:bool(np.all(a[m&(r<1.2*RS)]==1)) for n,a in masks.items()}})

if __name__=='__main__':main()
