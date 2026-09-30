import numpy as np, os, tifffile, time
from psd_tools import PSDImage
t0=time.time()
q=PSDImage.open(os.path.expanduser('~/Downloads/UnintCapes4.psb'))
lm=q._record.layer_and_mask_information
print('doc:', q.width, q.height, 'depth', q.depth, 'versió', q.version, 'ICC', len(q._record.image_resources.get_data(1039)), 'bytes | classic layer_info:', lm.layer_info.layer_count, '| blocs:', [k.name for k in lm.tagged_blocks.keys()], flush=True)
for i,l in enumerate(q):
    m=l.mask
    print(f'{i+1}. [{l.kind}] «{l.name[:70]}» bbox={l.bbox} blend={l.blend_mode.name} opac={l.opacity} vis={l.visible} màscara={m.bbox if m is not None else None}', flush=True)
CROPS={'costura dreta':(2600,2900,5000,5300),'sector graó (baix-esq)':(3200,3400,2900,3200),'corredor raig':(900,1100,2100,2400),'camp llunyà':(600,800,1200,1400),'marge estès dalt-esq':(100,300,100,300),'centre (Lluna)':(2600,2800,3900,4100)}
tif=tifffile.imread(os.path.expanduser('~/Downloads/Encaixada_2026-08-18/APILAT/APILAT_ESTESA_7648x5353_encaixada_VORESNETES_EXTENSIO_TANGENCIAL_MITJA.tif')).astype(np.float32)/65535
outs={k:np.zeros((y1-y0,x1-x0,3),np.float32) for k,(y0,y1,x0,x1) in CROPS.items()}
for l in q:
    if not l.visible: continue
    arr=l.numpy(); lx0,ly0,lx1,ly1=l.bbox
    mk=None
    if l.mask is not None and l.mask.bbox!=(0,0,0,0):
        mk=np.asarray(l.mask.topil()).astype(np.float32)/255.0; mx0,my0,mx1,my1=l.mask.bbox
    print(f'   capa «{l.name[:40]}» descodificada {arr.shape} en {time.time()-t0:.0f} s', flush=True)
    for k,(y0,y1,x0,x1) in CROPS.items():
        H,W=y1-y0,x1-x0; rgb=np.zeros((H,W,3),np.float32); a=np.zeros((H,W),np.float32)
        ix0,iy0,ix1,iy1=max(x0,lx0),max(y0,ly0),min(x1,lx1),min(y1,ly1)
        if ix1>ix0 and iy1>iy0:
            sub=arr[iy0-ly0:iy1-ly0, ix0-lx0:ix1-lx0]
            rgb[iy0-y0:iy1-y0, ix0-x0:ix1-x0]=sub[...,:3]; a[iy0-y0:iy1-y0, ix0-x0:ix1-x0]=sub[...,3] if sub.shape[-1]>3 else 1.0
        if mk is not None:
            mm=np.zeros((H,W),np.float32); jx0,jy0,jx1,jy1=max(x0,mx0),max(y0,my0),min(x1,mx1),min(y1,my1)
            if jx1>jx0 and jy1>jy0: mm[jy0-y0:jy1-y0, jx0-x0:jx1-x0]=mk[jy0-my0:jy1-my0, jx0-mx0:jx1-mx0]
            a=a*mm
        a=a*(l.opacity/255.0)
        out=outs[k]
        if l.blend_mode.name=='NORMAL': outs[k]=out*(1-a[...,None])+rgb*a[...,None]
        elif l.blend_mode.name=='LINEAR_LIGHT': outs[k]=out*(1-a[...,None])+np.clip(out+2*rgb-1,0,1)*a[...,None]
        else: raise SystemExit(l.blend_mode)
    del arr
for k,(y0,y1,x0,x1) in CROPS.items():
    c=outs[k]; t=tif[y0:y1,x0:x1]
    print(f'{k:26s} |composició − TIFF| màx {np.abs(c-t).max():.5f}  mediana {np.median(np.abs(c-t)):.6f}')
print('fet en', round(time.time()-t0), 's')
