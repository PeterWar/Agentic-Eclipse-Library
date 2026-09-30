"""Test low-order apparent-shape models on interleaved native limb sectors.
These are diagnostic image-geometry models, not attribution to the atmosphere.
No source pixels, contour mask, source grid or PSB are changed.
"""
from native_forward_common import *
from scipy.optimize import least_squares
from scipy.special import ndtr
from numpy.polynomial.legendre import leggauss
import ast,time

# Reuse the exact previously qualified native profile function without running
# the old script's measurements or overwriting any of its receipts.
origin=ROOT/'research/tools/earthshine_native_forward_20260911/c0_native_pose_audit.py';tree=ast.parse(origin.read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='profile_fit');exec(compile(ast.Module(body=[fn],type_ignores=[]),str(origin),'exec'))
old=json.loads((OUT/'C0_native_pose_profiles.json').read_text())['profiles'];ref='572A2976';stems=sorted(set(r['stem'] for r in old));edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');node,weight=leggauss(3);ox,oy=np.meshgrid(node/2,node/2);ow=(weight[:,None]*weight[None,:]/4).ravel();native_offsets=np.stack([ox.ravel(),oy.ravel()],1)
def design(angles,mode):
    th=np.deg2rad(angles);columns=[np.cos(th),np.sin(th)]
    if mode in ['similarity','affine']:columns.append(np.ones_like(th))
    if mode=='affine':columns.extend([np.cos(2*th),np.sin(2*th)])
    return np.stack(columns,axis=1)
oldlook={(r['stem'],r['angle']):r['fit'] for r in old};models={};fit_receipts=[]
for stem in stems:
    if stem==ref:continue
    obs=[]
    for angle in np.arange(30.,331.,15.):
        a=oldlook[stem,angle];b=oldlook[ref,angle]
        if a and b and a['qualified'] and b['qualified']:obs.append((angle,a['center']-b['center'],max(.05,np.hypot(a['center_se_conditional'],b['center_se_conditional']))))
    ar=np.array(obs);models[stem]={}
    for mode in ['rigid','similarity','affine']:
        A=design(ar[:,0],mode);fit=least_squares(lambda p:(A@p-ar[:,1])/ar[:,2],np.zeros(A.shape[1]),loss='soft_l1',f_scale=3);models[stem][mode]=fit.x;fit_receipts.append(dict(stem=stem,mode=mode,coefficients=fit.x.tolist(),training_rms=float(np.sqrt(np.mean((A@fit.x-ar[:,1])**2)))))
save('C3_shape_plan.json',dict(method=__doc__,reference=ref,stems=stems,fit_angles='30 to330deg step15, qualified existing C0 profiles',new_validation_angles='7.5 to352.5deg step15; native patches disjoint from C0 angular patches',angular_patch_half_width_rad='15/453.5',models='rigid dx,dy; similarity adds radius offset; affine adds cos2theta,sin2theta',interpretation='Descriptive local geometric distortions; no physical atmospheric attribution from a fit',promotion_gate='No PSB promotion. Affine candidate only if new-profile RMS improves20percent versus rigid overall and within each early,late,witness group; inspect right +/-30deg separately.',frozen_fits=fit_receipts))
new=[]
for stem in stems:
    start=time.time();z=np.load(SRC/f'A0_native_samples_{stem}.npz');dx=z['x']-CX;dy=z['y']-CY;theta=np.arctan2(dy,dx);radius=np.hypot(dx,dy);er=np.interp(theta%(2*np.pi),np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi);d=radius-er;valid=z['valid']&(z['q']>0)&np.isfinite(z['g'])&np.isfinite(z['variance'])&(z['variance']>0);offsets=native_offsets@z['native_to_world'].T
    for deg in np.arange(7.5,360,15):
        angle=np.deg2rad(deg);t=((theta-angle+np.pi)%(2*np.pi)-np.pi)*453.5;whole=(abs(d)<18)&(abs(t)<15);good=whole&valid;fraction=float(good.sum()/max(whole.sum(),1));fit=None
        if fraction>=.99 and good.sum()>=400:
            th=theta[good];no=np.cos(th)[:,None]*offsets[None,:,0]+np.sin(th)[:,None]*offsets[None,:,1];to=-np.sin(th)[:,None]*offsets[None,:,0]+np.cos(th)[:,None]*offsets[None,:,1];fit=profile_fit(d[good],t[good],z['g'][good],z['variance'][good],z['q'][good],no,to)
        new.append(dict(stem=stem,angle=float(deg),valid_fraction=fraction,fit=fit))
    save('C3_interleaved_profiles.json',dict(method=__doc__,profiles=new));print(stem,'profiles DONE',round(time.time()-start,2),flush=True)
look={(r['stem'],r['angle']):r['fit'] for r in new};comparisons=[]
for stem in stems:
    if stem==ref:continue
    for angle in np.arange(7.5,360,15):
        a=look[stem,angle];b=look[ref,angle]
        if a and b and a['qualified'] and b['qualified']:
            delta=a['center']-b['center'];pred={mode:float((design([angle],mode)@co).item()) for mode,co in models[stem].items()};group='witness' if stem in ['572A2968','572A2969','572A2970'] else 'early' if int(stem[-4:])<2990 else 'late';comparisons.append(dict(stem=stem,angle=float(angle),group=group,observed=delta,predicted=pred,residual={k:delta-v for k,v in pred.items()}))
summary=[]
for group in ['all','early','late','witness']:
    for region in ['all','right']:
        values=[r for r in comparisons if (group=='all' or r['group']==group) and (region=='all' or r['angle']<30 or r['angle']>330)]
        if values:summary.append(dict(group=group,region=region,n=len(values),rms={mode:float(np.sqrt(np.mean([r['residual'][mode]**2 for r in values]))) for mode in ['rigid','similarity','affine']}))
pass_group=all(s['rms']['affine']<.8*s['rms']['rigid'] for s in summary if s['region']=='all');save('C3_shape_validation.json',dict(method=__doc__,affine_geometry_candidate_PASS=pass_group,summary=summary,comparisons=comparisons,limits=['Interleaved pixels do not make the calibration, contour or profile model independent','Already investigated right-hand region: diagnostic model comparison, not blind astronomical discovery','Profile nuisance may mimic shape; no physical attribution or photographic correction promoted']))
print(json.dumps(dict(PASS=pass_group,summary=summary)),flush=True)
