"""Native lunar phase measured outside the withheld 435-449px region.
Frozen positive broad mixture; local step and exterior plane integrated over
native pixel aperture. Profile width is descriptive, not a recovered PSF.
No image, contour, source registration, or Photoshop layer is modified.
"""
from geometry_common import *
from scipy.optimize import least_squares
from scipy.special import ndtr
from numpy.polynomial.legendre import leggauss
import time
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
moon=float(np.load(PREV/'D2_auxiliary_corona.npz')['moon_level'])
angles=np.arange(0.,360.,15.)
node,weight=leggauss(3);ox,oy=np.meshgrid(node/2,node/2)
ow=(weight[:,None]*weight[None,:]/4).ravel();native_offsets=np.stack([ox.ravel(),oy.ravel()],1)
save('B0_plan.json',dict(method=__doc__,calibration=CAL,heldout=TEST,fit_region='native pixel centres r>=450px and d<18px; abs(tangent)<12px',p=P_WIDE,additional_sigma=12,minimum_valid_fraction=.99,phase_se_max=.3,scope='Separate outer-solar and lunar reference phases; no use of withheld 435-449 samples',prediction_gate=dict(minimum_qualified_sectors=12,minimum_heldout_sectors=8,heldout_rms_px=.25,angular_half_pose_gap_px=.30),model='Fixed deep-Moon level plus bounded local constant; mixture of narrow Gaussian step and additional Gaussian12; exterior radial/tangent plane; 3x3 native aperture quadrature'))
def profile_fit(d,t,values,var,q,no,to):
    amp=float(np.median(values[d>10])-moon)
    if amp<=100:return None
    yn=(values-moon)/amp;err=np.maximum(np.sqrt(var*14.826313721285086)/amp,.002)/np.sqrt(np.maximum(q,1e-5))
    def model(p):
        bg,A,dm,c,s,td=p;x=d[:,None]+no-c;T=t[:,None]+to;sw=np.hypot(s,12)
        f=ndtr(x/s);fw=ndtr(x/sw);F=(1-P_WIDE)*f+P_WIDE*fw
        H=(1-P_WIDE)*(x*f+s*np.exp(-.5*(x/s)**2)/np.sqrt(2*np.pi))+P_WIDE*(x*fw+sw*np.exp(-.5*(x/sw)**2)/np.sqrt(2*np.pi))
        return (bg+A*F+dm*H+td*T*F)@ow
    opt=least_squares(lambda p:(model(p)-yn)/err,[0,1,0,.3,1,0],bounds=([-.025,.3,-.2,-4,.35,-.1],[.025,3,.2,4,3.5,.1]),loss='soft_l1',f_scale=3,max_nfev=150,x_scale=[.01,1,.02,1,1,.01])
    res=(model(opt.x)-yn)/err;scatter=float(1.4826*np.median(abs(res-np.median(res))));cov=np.linalg.pinv(opt.jac.T@opt.jac)*max(scatter,1)**2;se=float(np.sqrt(max(cov[3,3],0)));qualified=bool(opt.success and abs(opt.x[3])<3.95 and .36<opt.x[4]<3.45 and se<.3 and np.linalg.matrix_rank(opt.jac)==6)
    return dict(center=float(opt.x[3]),sigma_descriptive=float(opt.x[4]),center_se_conditional=se,robust_weighted_scatter=scatter,relative_rms=float(np.sqrt(np.mean((model(opt.x)-yn)**2))),n=len(d),qualified=qualified,parameters=opt.x.tolist(),background_bound=bool(abs(opt.x[0])>.0249))
profiles=[]
for stem in CAL+TEST:
    start=time.time();z=np.load(SRC/f'A0_native_samples_{stem}.npz');dx=z['x']-CX;dy=z['y']-CY;theta=np.arctan2(dy,dx);radius=np.hypot(dx,dy);er=np.interp(theta%(2*np.pi),np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi);d=radius-er;valid=z['valid']&(z['q']>0)&np.isfinite(z['g'])&np.isfinite(z['variance'])&(z['variance']>0);offsets=native_offsets@z['native_to_world'].T
    for deg in angles:
        angle=np.deg2rad(deg);t=((theta-angle+np.pi)%(2*np.pi)-np.pi)*453.5;whole=(radius>=450)&(d<18)&(abs(t)<12);good=whole&valid;fraction=float(good.sum()/max(whole.sum(),1));fit=None
        if fraction>=.99 and good.sum()>=180 and np.min(d[good])<-.5:
            th=theta[good];no=np.cos(th)[:,None]*offsets[None,:,0]+np.sin(th)[:,None]*offsets[None,:,1];to=-np.sin(th)[:,None]*offsets[None,:,0]+np.cos(th)[:,None]*offsets[None,:,1];fit=profile_fit(d[good],t[good],z['g'][good],z['variance'][good],z['q'][good],no,to)
        profiles.append(dict(stem=stem,heldout=stem in TEST,angle=float(deg),valid_fraction=fraction,fit=fit))
    save('B0_lunar_profiles.json',dict(method=__doc__,moon_level=moon,profiles=profiles));print(stem,'qualified',sum(r['fit'] is not None and r['fit']['qualified'] for r in profiles if r['stem']==stem),'seconds',round(time.time()-start,2),flush=True)
