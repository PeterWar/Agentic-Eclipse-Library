"""Frozen global spatial operator: scene transfer and detector-null controls.
Actual spatial masks and shifts, original output weights, and cubic nuisance
projection are included. Covariance map/ridge are frozen at their training
values; this is a conditional differential operator test, not RAW chemistry.
"""
from common import *
import ast
import sys
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from scipy.fft import rfft2,irfft2
from scipy.sparse.linalg import LinearOperator,cg
claim();plan=json.loads((OUT/'PLAN.json').read_text());design=json.loads((OUT/'B3_G67_robust_design.json').read_text());names=design['names'];sh=np.array(design['shifts']);rad,theta=geometry();train=np.array([s in plan['pilot']['fit_vixen'] for s in names])
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');edge=gaussian_filter1d(edge,3,mode='wrap');er=np.interp(theta,np.linspace(0,2*np.pi,len(edge),endpoint=False),edge,period=2*np.pi);physical=rad<er
y,x=np.mgrid[:N,:N];xx=(x-CX)/455;yy=(y-CY)/455;basis=np.stack([xx**i*yy**j for i in range(4) for j in range(4-i)],-1);lowfit=(rad<410)&((theta//(np.pi/6)).astype(int)%2==0)
fy=np.fft.fftfreq(N)[:,None];fx=np.fft.rfftfreq(N)[None,:];f=np.hypot(fx,fy);u=np.clip((f-1/96)/(1/64-1/96),0,1);v=np.clip((f-1/16)/(1/12-1/16),0,1);H=(.5-.5*np.cos(np.pi*u))*(.5+.5*np.cos(np.pi*v))
maps=[]
for sx,sy in sh:
    ix=int(np.floor(sx));iy=int(np.floor(sy));qx=sx-ix;qy=sy-iy;maps.append([(iy,ix,(1-qy)*(1-qx)),(iy,ix+1,(1-qy)*qx),(iy+1,ix,qy*(1-qx)),(iy+1,ix+1,qy*qx)])
# Test the SAME forward/filter/adjoint function bodies as the production pilot.
tree=ast.parse((HERE/'b3_fpn_full.py').read_text());defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['filt','pull','push']]
exec(compile(ast.Module(body=defs,type_ignores=[]),str(HERE/'b3_fpn_full.py'),'exec'),globals())
weights=[]
for stem in names:
    z=np.load(OUT/'native'/('vixen_'+stem+'.npz'));q=(z['G1_q']+z['G2_q'])/2;a=(np.nan_to_num(z['G1'])*z['G1_q']+np.nan_to_num(z['G2'])*z['G2_q'])/np.maximum(2*q,1e-30)
    vv=(np.nan_to_num(z['G1_var'])*z['G1_q']**2+np.nan_to_num(z['G2_var'])*z['G2_q']**2)/np.maximum((2*q)**2,1e-30);good=np.isfinite(a)&np.isfinite(vv)&(q>0)&physical
    vs=gaussian_filter(np.where(good,vv,0),4)/np.maximum(gaussian_filter(good.astype(float),4),1e-30);weights.append(np.where(good,q/np.maximum(vs,1e-12),0))
OW=np.array(weights);del weights;variance=np.load(OUT/'arrays/B3_G67_robust_variance_field.npy');W=OW/(1+OW*variance[None])
full_safe='--full-safe' in sys.argv
if full_safe:
    from load_model_state import load_state
    state=load_state(['G','--all67','--robust','--hetero','--full-error-safe'])
    assert np.array_equal(OW,state['originalW']);W=state['W'];assert np.array_equal(H,state['H']);assert np.array_equal(sh,state['sh']);del state
den=W.sum(0);oden=OW.sum(0);td=OW[train].sum(0);lm=.1*np.median(den[(rad<300)&(den>0)])
def op(v):
    latent=v.reshape(N,N);D=filt(latent);pp=[pull(D,i) for i in range(len(names))];avg=sum(W[i]*p for i,p in enumerate(pp))/np.maximum(den,1e-30)
    result=sum(push(W[i]*(p-avg),i) for i,p in enumerate(pp));return (filt(result)+lm*latent).ravel()
A=LinearOperator((N*N,N*N),matvec=op,dtype=np.float64)
# Project each frame's low-frequency residual against exactly the same basis.
proj=[]
for i in range(len(names)):
    m=lowfit&(OW[i]>0);wt=OW[i,m];BB=basis[m];normal=BB.T@(BB*wt[:,None]);proj.append((m,np.linalg.inv(normal),wt))
def response(generator):
    ref=sum(OW[i]*generator(i) for i in np.flatnonzero(train))/np.maximum(td,1e-30);ref=np.where(td>0,ref,0)
    baseout=sum(OW[i]*generator(i) for i in range(len(names)))/np.maximum(oden,1e-30);Y=[]
    for i in range(len(names)):
        a=generator(i);m,ni,wt=proj[i];co=ni@(basis[m].T@((a[m]-ref[m])*wt));Y.append(a-basis@co)
    base=sum(W[i]*a for i,a in enumerate(Y))/np.maximum(den,1e-30);rhs=filt(sum(push(W[i]*(a-base),i) for i,a in enumerate(Y)));del Y
    rhsnorm=np.linalg.norm(rhs)
    if rhsnorm<1e-9:latent=np.zeros((N,N));info=0
    else:latent,info=cg(A,rhs.ravel(),rtol=2e-5,maxiter=60);latent=latent.reshape(N,N)
    assert info==0;D=filt(latent);correction=sum(OW[i]*pull(D,i) for i in range(len(names)))/np.maximum(oden,1e-30)
    return baseout-correction,baseout,rhsnorm
rng=np.random.default_rng(551309);rows=[];detrows=[];views={}
for j,wl in enumerate([18.,22.,28.,36.,44.,58.]):
    ang=rng.uniform(0,2*np.pi);ph=rng.uniform(0,2*np.pi);field=np.sin(2*np.pi*((x-CX)*np.cos(ang)+(y-CY)*np.sin(ang))/wl+ph)
    response_scene,base_scene,rn=response(lambda i:field)
    for lo,hi in plan['judge']['radii']:
        for sec in range(12):
            m=(rad>=lo)&(rad<hi)&((theta//(np.pi/6)).astype(int)==sec)&(oden>0);a=base_scene[m];b=response_scene[m];transfer=float(a@b/max(a@a,1e-30));err=float(np.linalg.norm(b-a)/max(np.linalg.norm(a),1e-30))
            rows.append(dict(injection=j,wavelength=wl,angle=ang,radius=[lo,hi],sector=sec,transfer=transfer,relative_error=err,pass_gate=.9<=transfer<=1.1))
    response_det,base_det,rn=response(lambda i:pull(field,i));m=(rad<410)&(rad>60)&(oden>0);ratio=float(np.linalg.norm(response_det[m])/np.linalg.norm(base_det[m]));detrows.append(dict(injection=j,wavelength=wl,angle=ang,residual_ratio=ratio,no_amplification=ratio<=1.1))
    if j in [0,5]:views['detector_before_'+str(j)]=base_det;views['detector_after_'+str(j)]=response_det
    print('INJECT',j,'wl',wl,'scene',min(q['transfer'] for q in rows if q['injection']==j),max(q['transfer'] for q in rows if q['injection']==j),'detector residual',ratio,flush=True)
np.savez_compressed(OUT/('arrays/B10_injection_views.npz' if full_safe else 'arrays/B7_injection_views.npz'),**views)
save('B10_global_injections_full_safe.json' if full_safe else 'B7_global_injections.json',dict(method=__doc__,scene=rows,detector_only=detrows,all_scene_pass=all(q['pass_gate'] for q in rows),all_detector_no_amplification=all(q['no_amplification'] for q in detrows),covariance_sha256=sha(OUT/'arrays/B3_G67_robust_hetero_full_safe_variance_field.npy' if full_safe else OUT/'arrays/B3_G67_robust_variance_field.npy'),model_script_sha256=sha(HERE/'b3_fpn_full.py'),full_safe=full_safe,limits=['Differential operator on calibrated registered G, not a new absolute RAW-to-display test','Covariance and ridge frozen; detector perturbations do not retrain stochastic error estimates','Scene injection passes in a free-scene model by construction; detector-only controls and external comparison remain essential']))
