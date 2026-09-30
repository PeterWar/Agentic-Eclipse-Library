from pathlib import Path
import json,time
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,map_coordinates,binary_erosion
from scipy.optimize import minimize
O=Path('/private/tmp/v105_base_sources_20260926');D=Path('/private/tmp/eclipse_v104_diagnosi_20260926')
q=np.load(O/'572A2975.npz');by,ey,bx,ex=map(int,q['box']);box=[by,ey,bx,ex];shape=(ey-by,ex-bx)
a=np.load(D/'L303.npz');ref=np.stack([a[f'c{c}'] for c in range(3)],-1)[by-3000:ey-3000,bx-4600:ex-4600].astype(np.float32)/65535
yy,xx=np.mgrid[by:ey,bx:ex];cx,cy=5361.768111973117,3775.747534140857
d=np.hypot(xx-5375.786804312011,yy-3775.9774911631)-452.9785129274736
theta=np.degrees(np.arctan2(-(yy-cy),xx-cx))%360;sectors=(theta//30).astype(int)
def texture(img,sig=(1,4)):
    valid=np.isfinite(img)&(img>0)
    l=np.where(valid,np.log(np.maximum(np.nan_to_num(img),1e-9)),0)
    # Numerical extension only for registration. No extension exported as data.
    def g(s):return gaussian_filter(l,s,truncate=4)/np.maximum(gaussian_filter(valid.astype(float),s,truncate=4),1e-12)
    t=(g(sig[0])-g(sig[1])).astype(np.float32)
    safe=binary_erosion(valid,iterations=int(4*sig[1])+2)
    return t,safe
def corr(x,y):
    return float(np.corrcoef(x,y)[0,1]) if len(x)>10 else None
def fit_sim(template,input_img,mask,source_center,target_center,p0,bounds,label,coarse_angles=None):
    ti,vs=texture(input_img);tt,vt=texture(template)
    mask=mask&vt
    fit=mask&(sectors%2==0);hold=mask&(sectors%2==1)
    iy,ix=np.where(fit);stride=max(1,len(ix)//60000);iy=iy[::stride];ix=ix[::stride]
    px=ix+bx-target_center[0];py=iy+by-target_center[1];target=tt[iy,ix].astype(float)
    def coords(p,x,y):
        ang=np.deg2rad(p[2]);sc=p[3]
        # p is target->source sampling; dx/dy are in source pixels.
        return (source_center[0]+p[0]+sc*(np.cos(ang)*x-np.sin(ang)*y),source_center[1]+p[1]+sc*(np.sin(ang)*x+np.cos(ang)*y))
    def objective(p):
        sx,sy=coords(p,px,py);v=map_coordinates(ti,[sy,sx],order=1,mode='constant',cval=0,prefilter=False)
        valid=map_coordinates(vs.astype(np.uint8),[sy,sx],order=0,mode='constant',cval=0,prefilter=False)>0
        return 1-corr(target[valid],v[valid]) if valid.mean()>.9 else 1
    if coarse_angles is not None:
        trials=[]
        for ang in coarse_angles:
            p=list(p0);p[2]=float(ang);trials.append((objective(p),p))
        trials.sort();p0=trials[0][1];print(label,'coarse',trials[:4],flush=True)
    opt=minimize(objective,np.array(p0,dtype=float),method='Powell',bounds=bounds,options={'maxiter':80,'xtol':.00005,'ftol':1e-9})
    p=opt.x
    sx,sy=coords(p,xx-target_center[0],yy-target_center[1]);m=map_coordinates(vs.astype(np.uint8),[sy,sx],order=0,mode='constant',cval=0,prefilter=False)>0
    warped=map_coordinates(ti,[sy,sx],order=1,mode='constant',cval=0,prefilter=False)
    sx0,sy0=coords(p0,xx-target_center[0],yy-target_center[1]);before=map_coordinates(ti,[sy0,sx0],order=1,mode='constant',cval=0,prefilter=False)
    rows=[]
    for k in range(12):
        z=mask&m&(sectors==k);rows.append({'sector_deg':[k*30,(k+1)*30],'held_out':bool(k%2),'n':int(z.sum()),'before':corr(tt[z],before[z]),'after':corr(tt[z],warped[z])})
    out={'label':label,'parameters_sampling_dx_dy_angle_deg_scale':p.tolist(),'initial_parameters':p0,'source_center_local':source_center,'target_center_canvas':target_center,'optimizer_success':bool(opt.success),'fit_ncc':corr(tt[fit&m],warped[fit&m]),'held_out_ncc':corr(tt[hold&m],warped[hold&m]),'ncc_before_fit':corr(tt[fit&m],before[fit&m]),'ncc_before_held_out':corr(tt[hold&m],before[hold&m]),'sectors':rows,'fit_domain':'physical/model and presentation limb excluded >=20px; green log DoG 1,4 px truncate4; 30deg even sectors fit, odd held out','source_support':'bilinear source bounds and finite input; no physical support assertion'}
    # homogeneous transform from target canvas to source local coordinates
    ang=np.deg2rad(p[2]);sc=p[3];A=sc*np.array([[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]]);b=np.asarray(source_center)+p[:2]-A@target_center
    H=np.eye(3);H[:2,:2]=A;H[:2,2]=b;out['target_canvas_to_source_local']=H.tolist();out['source_local_to_target_canvas']=np.linalg.inv(H).tolist()
    (O/f'{label}_registration.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True)
    return out,sx,sy
raw=q['E'];valid=q['valid_rgb']&(q['dreal']>20)&(d>20)&(d<150)&(ref[...,1]>.02)&(ref[...,1]<.90)
rawfit,sx,sy=fit_sim(raw[...,1],ref[...,1],valid,[cx-bx,cy-by],[cx,cy],[0,0,0,1],[(-12,12),(-12,12),(-2,2),(.97,1.03)],'current303_to_E2975')
reg=np.stack([map_coordinates(ref[...,c],[sy,sx],order=1,mode='constant',cval=np.nan,prefilter=False) for c in range(3)],-1).astype(np.float32)
support=np.isfinite(reg).all(-1);np.savez_compressed(O/'current303_registered_to_E2975.npz',RGB=reg,support=support,box=box,metadata_json=json.dumps(rawfit))
src=np.load(O/'09_original_CapesInteriors_RGB.npy',mmap_mode='r');ox,oy=2764,1475;crop=src[oy:oy+1600,ox:ox+1600].astype(np.float32)/65535
originalfit,sx,sy=fit_sim(ref[...,1],crop[...,1],(d>25)&(d<150)&(ref[...,1]>.02)&(ref[...,1]<.90),[3563.8912793889317-ox,2274.660453669-oy],[cx,cy],[0,0,0,1/1.03],[(-20,20),(-20,20),(-20,20),(.93,1.02)],'original09_to_current303',np.arange(-20,20.01,.5))
reg=np.stack([map_coordinates(crop[...,c],[sy,sx],order=1,mode='constant',cval=np.nan,prefilter=False) for c in range(3)],-1).astype(np.float32)
support=np.isfinite(reg).all(-1);originalfit['source_crop_xy']=[ox,oy];np.savez_compressed(O/'original09_registered_to_current303.npz',RGB=reg,support=support,box=box,metadata_json=json.dumps(originalfit))
# Chain current303 canvas coordinates sampled by E2975 -> original source crop.
Hraw=np.array(rawfit['target_canvas_to_source_local']);Hraw[:2,2]+=[bx,by]
Horg=np.array(originalfit['target_canvas_to_source_local']);H=Horg@Hraw
sx=H[0,0]*xx+H[0,1]*yy+H[0,2];sy=H[1,0]*xx+H[1,1]*yy+H[1,2]
reg=np.stack([map_coordinates(crop[...,c],[sy,sx],order=1,mode='constant',cval=np.nan,prefilter=False) for c in range(3)],-1).astype(np.float32);support=np.isfinite(reg).all(-1)
meta={'kind':'display-referred observed original09, not calibrated radiance','source':'09_original_CapesInteriors_RGB.npy','source_crop_xy':[ox,oy],'target_canvas_to_source_crop':H.tolist(),'chain':['original09_to_current303','current303_to_E2975'],'interpolation':'bilinear one direct sampling of original source','no_moon_alignment':True}
np.savez_compressed(O/'original09_registered_to_E2975.npz',RGB=reg,support=support,box=box,metadata_json=json.dumps(meta))
