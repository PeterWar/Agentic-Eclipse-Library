from pathlib import Path
p=Path('/private/tmp/v105_base_sources_20260926/register_sources.py');ns={};exec(p.read_text().split('raw=q[\'E\']')[0],ns);globals().update(ns)
src=np.load(O/'09_original_CapesInteriors_RGB.npy',mmap_mode='r');ox,oy=2764,1475;crop=src[oy:oy+1600,ox:ox+1600].astype(np.float32)/65535
p0=[6.74177789,-11.90427481,11.60544035,1/1.01946242]
r,sx,sy=fit_sim(ref[...,1],crop[...,1],(d>25)&(d<150)&(ref[...,1]>.02)&(ref[...,1]<.90),[3563.8912793889317-ox,2274.660453669-oy],[cx,cy],p0,[(2,11),(-17,-7),(11,12.2),(.974,.987)],'original09_bboxseed_to_current303')
reg=np.stack([map_coordinates(crop[...,c],[sy,sx],order=1,mode='constant',cval=np.nan,prefilter=False) for c in range(3)],-1).astype(np.float32);support=np.isfinite(reg).all(-1)
r['source_crop_xy']=[ox,oy];np.savez_compressed(O/'original09_bboxseed_registered_to_current303.npz',RGB=reg,support=support,box=box,metadata_json=json.dumps(r))
Hraw=np.array(json.loads((O/'current303_to_E2975_registration.json').read_text())['target_canvas_to_source_local']);Hraw[:2,2]+=[bx,by]
Horg=np.array(r['target_canvas_to_source_local']);H=Horg@Hraw
sx=H[0,0]*xx+H[0,1]*yy+H[0,2];sy=H[1,0]*xx+H[1,1]*yy+H[1,2]
reg=np.stack([map_coordinates(crop[...,c],[sy,sx],order=1,mode='constant',cval=np.nan,prefilter=False) for c in range(3)],-1).astype(np.float32);support=np.isfinite(reg).all(-1)
meta={'kind':'display-referred observed original09, not calibrated radiance','source':'09_original_CapesInteriors_RGB.npy','source_crop_xy':[ox,oy],'target_canvas_to_source_crop':H.tolist(),'chain':['original09_bboxseed_to_current303','current303_to_E2975'],'interpolation':'bilinear one direct sampling of original source','no_moon_alignment':True,'registration_status':'consult held-out correlations'}
np.savez_compressed(O/'original09_bboxseed_registered_to_E2975.npz',RGB=reg,support=support,box=box,metadata_json=json.dumps(meta))
