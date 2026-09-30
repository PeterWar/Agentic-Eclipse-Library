"""Quantify saved appearance in fixed corona context and verify native ablations."""
from reveal_common import *
import tifffile,gc
from PIL import Image
from scipy.ndimage import map_coordinates
meta=json.loads((OUT/'A1_native_ablation.json').read_text());rois={};receipts=[]
for key,path in meta['files'].items():
    with tifffile.TiffFile(path) as tf:a=tf.asarray();extras=list(map(int,tf.pages[0].extrasamples))
    assert a.dtype==np.uint16 and a.shape[:2]==(7506,10551)
    roi=a[Y0:Y0+N,X0:X0+N,:3].copy()
    if a.shape[-1]==4:assert np.all(a[Y0:Y0+N,X0:X0+N,3]==65535)
    rois[key]=roi;np.save(OUT/f'A2_{key}_RGB16.npy',roi)
    full=a[::4,::4,:3]
    if a.shape[-1]==4:full=np.rint(full.astype(float)*65535/np.maximum(a[::4,::4,3,None],1)).clip(0,65535).astype('uint16')
    Image.fromarray((full>>8).astype('uint8')).save(OUT/f'A2_{key}_llenc.png');Image.fromarray((roi>>8).astype('uint8')).save(OUT/f'A2_{key}_lluna.png')
    receipts.append(dict(key=key,path=path,shape=list(a.shape),extrasamples=extras,sha256=sha(path)));del a;gc.collect()
cur=rois['Pere_actual'].astype(float);old=rois['font_anterior_context_actual'].astype(float);bg=rois['sense_font_lunar'].astype(float);src=np.load(OUT/'A0_Pere_moon_RGB16.npy').astype(float);prev=np.load(OUT/'A0_previous_moon_RGB16.npy').astype(float);mask=np.load(OUT/'A0_inherited_mask_roi.npy').astype(float)/65535
expected=src*mask[...,None]+bg*(1-mask[...,None]);expected_old=prev*mask[...,None]+bg*(1-mask[...,None]);err=np.max(abs(cur-expected));err_old=np.max(abs(old-expected_old));delta_err=np.max(abs((cur-old)-(src-prev)*mask[...,None]));assert max(err,err_old,delta_err)<=6,(err,err_old,delta_err)
yy,xx=np.mgrid[:N,:N];rad=np.hypot(xx-CX,yy-CY);angle=np.arctan2(yy-CY,xx-CX)%(2*np.pi);edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');dist=rad-np.interp(angle,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi)
sectors=[]
for sector in range(12):
    angle_sel=(angle>=sector*2*np.pi/12)&(angle<(sector+1)*2*np.pi/12)
    for lo,hi in [(-80,-30),(-25,-6),(-3,0),(0,3)]:
        use=angle_sel&(dist>=lo)&(dist<hi);sectors.append(dict(sector=sector,distance=[lo,hi],pixels=int(use.sum()),median_current_G=float(np.median(cur[...,1][use])),median_previous_G=float(np.median(old[...,1][use])),median_without_source_G=float(np.median(bg[...,1][use])),median_mask=float(np.median(mask[use])),median_delta_G=float(np.median((cur-old)[...,1][use]))))
points=[]
for d in np.arange(-40,16,.5):
    use=(dist>=d)&(dist<d+.5);points.append(dict(distance=float(d+.25),current_G=float(np.median(cur[...,1][use])),old_context_G=float(np.median(old[...,1][use])),without_source_G=float(np.median(bg[...,1][use])),source_G=float(np.median(src[...,1][use])),mask=float(np.median(mask[use]))))
save('A2_composition.json',dict(method=__doc__,native_export_receipts=receipts,recomposition_max_DN16=float(err),old_recomposition_max_DN16=float(err_old),delta_prediction_max_DN16=float(delta_err),sectors=sectors,radial_profile=points,interpretation='On the saved photographic context, lunar RGB change plus unchanged mask explains the native before/after composition within rounding. This localizes the source of display change; it does not identify a unique optical PSF.',no_new_source=True))
print('COMPOSITION VERIFIED',err,err_old,delta_err,flush=True)
