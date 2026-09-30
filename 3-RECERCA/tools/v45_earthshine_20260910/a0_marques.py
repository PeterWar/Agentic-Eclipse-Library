from comu45 import *
import tifffile,hashlib
from scipy.ndimage import label,find_objects,binary_dilation

claim45()
src=Path('/Users/USUARI/Downloads/Earthshine_V44_artefactes.tif')
with tifffile.TiffFile(src) as tf:
    a=tf.asarray();extras=[int(x) for x in tf.pages[0].extrasamples]
assert a.shape==(H,W,3) and a.dtype==np.uint16
roi=a[Y0:Y0+N,X0:X0+N].astype(np.float32)/65535
np.save(CAU45/'annotated_rgb.npy',roi)
png45('A0_anotat_lluna_1a1.png',roi)
png45('A0_anotat_llenc_quart.png',a[::4,::4].astype(np.float32)/65535)
rgb=roi
masks=dict(blau_clar=(rgb[...,2]>.08)&(rgb[...,1]>.08)&(rgb[...,0]<rgb[...,1]*.78)&(rgb[...,0]<rgb[...,2]*.75),
           lila=(rgb[...,0]>.035)&(rgb[...,2]>.035)&(rgb[...,1]<np.minimum(rgb[...,0],rgb[...,2])*.78))
report=dict(path=str(src),sha256=sha(src),shape=list(a.shape),dtype=str(a.dtype),extras=extras,roi_origin=[X0,Y0],marks={})
for name,m in masks.items():
    np.save(CAU45/(name+'_mask.npy'),m)
    lab,n=label(m);rows=[]
    for i,sl in enumerate(find_objects(lab),1):
        if sl is None:continue
        q=lab[sl]==i;count=int(q.sum())
        if count<8:continue
        ys,xs=sl;cy,cx=np.where(q);cx=cx+xs.start;cy=cy+ys.start
        rows.append(dict(n=count,bbox=[X0+xs.start,Y0+ys.start,X0+xs.stop,Y0+ys.stop],radius_percentiles=np.percentile(R[cy,cx],[0,10,50,90,100]).tolist(),angle_degrees=np.percentile(np.degrees(PHI[cy,cx]),[10,50,90]).tolist()))
    report['marks'][name]=dict(pixels=int(m.sum()),components=rows)
savejson(REB45/'A0_marques.json',report)
print(json.dumps(report,ensure_ascii=False),flush=True)
