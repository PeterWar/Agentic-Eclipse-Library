"""Observed RAW pilot: common saturation window, no noisy-signal floor.
No T, extrapolation, channel filling, or spatial radiance correction.
Physical selection uses each frame's measured silhouette, not display alpha.
"""
import argparse,json,hashlib,sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d,maximum_filter1d
R=Path('/Users/USUARI/Desktop/Eclipse 2026')
O=Path('/private/tmp/v105_root_pilots_20260926')
def smooth(x,a,b):
    z=np.clip((x-a)/(b-a),0,1);return z*z*(3-2*z)
def run():
    ap=argparse.ArgumentParser();ap.add_argument('--tag',default='P01');ap.add_argument('--lo',type=float,default=.6);ap.add_argument('--hi',type=float,default=2.);ap.add_argument('--undo-phi',action='store_true');a=ap.parse_args()
    out=O/a.tag;assert not out.exists();out.mkdir()
    src=Path('/private/tmp/v105_raw_pilot_20260926/no_floor_all67')
    meta=json.loads((src/'METADATA.json').read_text());oldpath=R/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A3C_franja_silueta.npz';oq=np.load(oldpath)
    y0,y1,x0,x1=map(int,meta['box_y0y1x0x1']);yy,xx=np.mgrid[y0:y1,x0:x1];cx,cy,rad=oq['centre'];h,w=yy.shape
    d=(np.hypot(xx-cx,yy-cy)-rad).astype(np.float32);theta=np.degrees(np.arctan2(-(yy-cy),xx-cx))%360
    sil=np.load(R/'4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz');rm=meta['radius_model']
    N=np.load(src/'numerator.npy',mmap_mode='r');W=np.load(src/'weight.npy',mmap_mode='r');D=np.load(src/'distance_model.npy',mmap_mode='r')
    ns=np.zeros((h,w,3),float);ws=np.zeros_like(ns);nf=np.zeros((h,w),np.int16);sw2=np.zeros((h,w));shortw=np.zeros((h,w));dmax=np.full((h,w),-100.,np.float32)
    # Provisional pooled constant gains, never affine offsets. QA retained.
    gains_short=np.array([1.0450957561806684,1.0395079772315399,1.0436351869797877])
    if a.undo_phi:
        sys.path.insert(0,'/private/tmp/v105_qa_20260926');from p02_phi_helpers import phi_crop,numerator_remove_phi_keep_b
        cau=R/'4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v36/cau'
        oldmeta=json.loads((cau/'vixen_meta.json').read_text());phigrids={c:np.load(cau/f'vixen_{c}_phi.npy',mmap_mode='r')for c in 'RGB'}
        gains_short=np.array([1.0449916196505562,1.0323935150021668,0.9904648104154337])
    for j,frame in enumerate(meta['frames']):
        dm=np.asarray(D[j],np.float64);iy,ix=h//2,w-100
        gx=(dm[iy,ix+1]-dm[iy,ix-1])/2;gy=(dm[iy+1,ix]-dm[iy-1,ix])/2
        cxf=ix+x0-(dm[iy,ix]+rm)*gx;cyf=iy+y0-(dm[iy,ix]+rm)*gy
        pa=np.degrees(np.arctan2(-(yy-cyf),xx-cxf))%360
        dr=(dm+(rm-rad)-np.interp(pa.ravel(),sil['pa'],sil['e'],period=360).reshape(h,w)).astype(np.float32)
        gate=smooth(dr,a.lo,a.hi);weight=np.asarray(W[j]);num=np.asarray(N[j]);ok=np.all(np.isfinite(num)&np.isfinite(weight)&(weight>0),-1)
        gate*=ok;gains=gains_short if frame['name'] in [f'572A{i}.CR3' for i in range(2959,2967)] else np.ones(3)
        if a.undo_phi:
            oj=frame['original_index'];assert oldmeta['frames'][oj]['name']==frame['name']
            phi=np.stack([phi_crop(phigrids[c][oj],[y0,y1,x0,x1],oldmeta['Q'])for c in 'RGB'],-1)
            num=numerator_remove_phi_keep_b(num,phi)
        ns+=np.where(ok[...,None],num*gains,0)*gate[...,None];ws+=np.where(ok[...,None],weight,0)*gate[...,None]
        wg=weight[...,1]*gate;sw2+=wg*wg;nf+=(gate>0);dmax=np.where(gate>0,np.maximum(dmax,dr),dmax)
        if frame['exposure']<=1/800:shortw+=wg
    cam=np.divide(ns,ws,out=np.zeros_like(ns),where=ws>0)
    E=np.einsum('ij,hwj->hwi',np.asarray(meta['matrix']),cam*np.asarray(meta['gain'])).astype(np.float32)
    # A negative post-matrix primary can be an out-of-gamut red feature.
    # It is not missing observation and must not move a geometric boundary.
    observed=np.all(ws>0,axis=-1)&np.all(np.isfinite(E),axis=-1)
    filter_valid=observed&(nf>=3)&(ws[...,1]>=1.5*min(f['exposure']for f in meta['frames']))
    nb=1440;ib=(theta/360*nb).astype(int)%nb;zone=(d>-40)&(d<20);dmin=np.full(nb,np.nan)
    for k in range(nb):
        z=zone&(ib==k);bad=d[z&~filter_valid]
        dmin[k]=bad.max()+.25 if len(bad) else (d[z].min() if z.any()else np.nan)
    ok=np.isfinite(dmin);dmin[~ok]=np.interp(np.flatnonzero(~ok),np.flatnonzero(ok),dmin[ok],period=nb)
    dmin=np.maximum(gaussian_filter1d(maximum_filter1d(dmin,5,mode='wrap'),4,mode='wrap'),maximum_filter1d(dmin,3,mode='wrap')).astype(np.float32)
    domnew=filter_valid&(d>=dmin[ib])&(d>=0)
    mix=(1-smooth(d,12,25));oldvalid=oq['domini_E'];mix=np.where(~oldvalid,1,mix)*observed
    hybrid=np.where((mix>0)[...,None],(1-mix[...,None])*oq['E']+mix[...,None]*E,oq['E']).astype(np.float32)
    cfg=json.loads((oldpath.parent/'A3C_FRANJA_SILUETA.json').read_text());sc=cfg['escales']
    q={k:oq[k] for k in ['box','centre','G','F','V','domini','domini_E','beta','dins_franja']}
    replace=d<25
    for c in range(3):q['F'][...,c]=np.where(replace,hybrid[...,c]*sc[f'c_F{c}'][0],q['F'][...,c])
    q['G']=np.where(replace,hybrid[...,1]*sc['c_G'][0],q['G']).astype(np.float32)
    q['V']=np.where(replace,hybrid[...,1]*sc['c_V'][0],q['V']).astype(np.float32)
    for key in ['domini','domini_E']:q[key]=np.where(replace,domnew,q[key])
    q['domini']=q['domini']&(q['G']>0)
    q['beta']=np.where(replace,domnew.astype(np.float32),q['beta']);q['dins_franja']=q['beta']>0
    q.update(E=hybrid,E_observed=E,observed=observed,NF=nf,DMIN=dmin,DREAL_MAX=dmax,NEFF=np.divide(ws[...,1]**2,sw2,out=np.zeros_like(sw2),where=sw2>0).astype(np.float32),short_fraction=np.divide(shortw,ws[...,1],out=np.zeros_like(shortw),where=ws[...,1]>0).astype(np.float32),W=ws.astype(np.float32),physical_ramp=np.array([a.lo,a.hi]))
    dst=out/'Q_OBSERVED.npz';np.savez_compressed(dst,**q)
    rep={'source':str(src),'source_receipt':str(src/'COMPLETE.json'),'noisy_floor_removed':True,'physical_ramp':[a.lo,a.hi],'T_correction':False,'spatial_fill':False,'short_camera_gain':gains_short.tolist(),'short_calibration_status':'PROVISIONAL; heldout residual up to several percent remains, see pooled QA','E_old_join':[12,25],'DMIN_old_new':{str(deg):[float(oq['DMIN'][int(deg/360*nb)]),float(dmin[int(deg/360*nb)])]for deg in range(0,360,30)},'new_filter_pixels_dlt25':int((q['domini']&~oq['domini']&(d<25)).sum()),'lost_filter_pixels_dlt25':int((~q['domini']&oq['domini']&(d<25)).sum()),'observed_pixels':int(observed.sum()),'output':str(dst)}
    # Verify exact preservation of the old full pipeline input outside the join.
    for key in ['F','G','V','domini']:
        assert np.array_equal(q[key][d>=25],oq[key][d>=25],equal_nan=True),key
    rep['frozen_phi_removed_all_frames']=a.undo_phi
    rep['weight_note']='Per-camera-channel W is frozen saturation weight times exposure; Green sums two CFA planes, so 1.5*short exposure threshold equals .75 fully weighted green frame.'
    if a.undo_phi:rep['calibration_receipt']='/private/tmp/v105_qa_20260926/P02_FROZEN_CONFIG.json'
    (out/'COMBINE.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep,indent=2),flush=True)
if __name__=='__main__':run()
