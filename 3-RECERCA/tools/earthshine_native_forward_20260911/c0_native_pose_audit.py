"""Measure residual rigid lunar pose using sectors outside the right-hand pilot.
Fit uncensored native green samples with a pixel-integrated Gaussian step and
two planar backgrounds. Relative centres cancel common contour shape bias.
This is a geometry audit; no source warp or PSB mask is changed.
"""
from native_forward_common import *
from scipy.optimize import least_squares
from scipy.special import ndtr
from numpy.polynomial.legendre import leggauss
import time
ref='572A2976';stems=['572A2973','572A2974','572A2975',ref,'572A2991','572A2992','572A2993','572A2994','572A2968','572A2969','572A2970'];witness=['572A2968','572A2969','572A2970'];angles=np.arange(0.,360.,15.);edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');node,weight=leggauss(3);ox,oy=np.meshgrid(node/2,node/2);ow=(weight[:,None]*weight[None,:]/4).ravel();native_offsets=np.stack([ox.ravel(),oy.ravel()],1);profiles=[]
save('C0_pose_plan.json',dict(method=__doc__,reference=ref,stems=stems,new_epoch_witness=witness,fit_sectors='30 through330deg inclusive; right-hand0,+/-15deg held out from rigid-pose estimation',parameters='Relative dx,dy only; no per-frame radius fit or source modification',profile='Native pixel aperture3x3 GL, Gaussian optical core and two planar backgrounds; descriptive, not unique PSF',scope='Spatially withheld pose prediction conditional on existing calibration; no claim of full RAW independence'))
def profile_fit(d,t,values,var,q,normal_offset,tangent_offset):
    base=float(np.median(values[d<-10]));amp=float(np.median(values[d>10])-base)
    if amp<=0:return None
    yn=(values-base)/amp;err=np.maximum(np.sqrt(var)/amp,.002)/np.sqrt(np.maximum(q,1e-5))
    def model(p):
        bg,mi,A,dm,c,s,ti,td=p;x=d[:,None]+normal_offset-c;T=t[:,None]+tangent_offset;F=ndtr(x/s);phi=np.exp(-.5*(x/s)**2)/np.sqrt(2*np.pi)
        return (bg+mi*x+A*F+dm*(x*F+s*phi)+T*(ti+td*F))@ow
    opt=least_squares(lambda p:(model(p)-yn)/err,[0,0,1,0,.5,1,0,0],bounds=([-1,-.2,.1,-.3,-4,.35,-.2,-.3],[1,.2,5,.3,4,4,.2,.3]),loss='soft_l1',f_scale=3,max_nfev=180)
    res=(model(opt.x)-yn)/err;scatter=float(1.4826*np.median(abs(res-np.median(res))));cov=np.linalg.pinv(opt.jac.T@opt.jac)*max(scatter,1)**2;se=float(np.sqrt(max(cov[4,4],0)));qualified=bool(opt.success and abs(opt.x[4])<3.95 and .36<opt.x[5]<3.95 and se<.3)
    return dict(center=float(opt.x[4]),sigma_optical_descriptive=float(opt.x[5]),center_se_conditional=se,robust_weighted_scatter=scatter,relative_rms=float(np.sqrt(np.mean((model(opt.x)-yn)**2))),n=len(d),qualified=qualified,parameters=opt.x.tolist())
for stem in stems:
    start=time.time();z=np.load(SRC/f'A0_native_samples_{stem}.npz');dx=z['x']-CX;dy=z['y']-CY;theta=np.arctan2(dy,dx);radius=np.hypot(dx,dy);er=np.interp(theta%(2*np.pi),np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi);d=radius-er;valid=z['valid']&(z['q']>0)&np.isfinite(z['g'])&np.isfinite(z['variance'])&(z['variance']>0);offsets=native_offsets@z['native_to_world'].T
    for deg in angles:
        angle=np.deg2rad(deg);t=((theta-angle+np.pi)%(2*np.pi)-np.pi)*453.5;whole=(abs(d)<18)&(abs(t)<15);good=whole&valid;nwhole=int(whole.sum());fraction=float(good.sum()/max(nwhole,1));fit=None
        if fraction>=.99 and good.sum()>=400:
            th=theta[good];no=np.cos(th)[:,None]*offsets[None,:,0]+np.sin(th)[:,None]*offsets[None,:,1];to=-np.sin(th)[:,None]*offsets[None,:,0]+np.cos(th)[:,None]*offsets[None,:,1];fit=profile_fit(d[good],t[good],z['g'][good],z['variance'][good],z['q'][good],no,to)
        profiles.append(dict(stem=stem,angle=float(deg),valid_fraction=fraction,fit=fit))
    save('C0_native_pose_profiles.json',dict(method=__doc__,profiles=profiles));print(stem,'qualified',sum(r['fit'] is not None and r['fit']['qualified'] for r in profiles if r['stem']==stem),'seconds',round(time.time()-start,2),flush=True)
lookup={(r['stem'],r['angle']):r['fit'] for r in profiles};poses=[]
for stem in stems:
    if stem==ref:continue
    rr=[]
    for deg in angles:
        a=lookup[stem,float(deg)];b=lookup[ref,float(deg)]
        if a and b and a['qualified'] and b['qualified']:rr.append(dict(angle=float(deg),difference=a['center']-b['center'],error=max(.05,np.hypot(a['center_se_conditional'],b['center_se_conditional']))))
    training=[r for r in rr if 30<=r['angle']<=330];test=[r for r in rr if r not in training]
    if len(training)<8:poses.append(dict(stem=stem,status='INSUFFICIENT_OUTSIDE_SECTORS',available=len(training)));continue
    ang=np.deg2rad([r['angle'] for r in training]);A=np.stack([np.cos(ang),np.sin(ang)],1);b=np.array([r['difference'] for r in training]);err=np.array([r['error'] for r in training]);opt=least_squares(lambda p:(A@p-b)/err,np.zeros(2),loss='soft_l1',f_scale=3);delta=opt.x
    for r in rr:
        v=np.array([np.cos(np.deg2rad(r['angle'])),np.sin(np.deg2rad(r['angle']))]);r['prediction']=float(v@delta);r['residual']=r['difference']-r['prediction'];r['opposite_residual']=r['difference']+r['prediction']
    tests=[r for r in rr if r['angle']<30 or r['angle']>330];poses.append(dict(stem=stem,status='DESCRIPTIVE_POSE',relative_to=ref,dx=float(delta[0]),dy=float(delta[1]),fit_sectors=len(training),fit_rms_px=float(np.sqrt(np.mean((A@delta-b)**2))),new_epoch_witness=stem in witness,heldout_right=tests,all_sectors=rr))
save('C0_native_pose_audit.json',dict(method=__doc__,reference=ref,poses=poses,limits=['Approximate locally straight profile with nuisance backgrounds; no unique optical PSF','Only complete uncensored sectors used; long saturated exposures not assigned a pose from a censored maximum','Relative pose evidence only, no source registration promoted','Right-hand predictions are spatial withholding conditional on prior global calibration and shared observed contour']))
print(json.dumps([{k:r.get(k) for k in ['stem','status','dx','dy','fit_rms_px','heldout_right']} for r in poses]),flush=True)
