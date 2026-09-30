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
claim();from prior_state import load_state
st=load_state('R');plan=json.loads((OUT/'PLAN.json').read_text());names=st['names'];sh=st['sh'];rad,theta=geometry();train=st['train'];physical=st['physical'];y,x=np.mgrid[:N,:N];xx=(x-CX)/455;yy=(y-CY)/455;basis=np.stack([xx**i*yy**j for i in range(4) for j in range(4-i)],-1);lowfit=st['lowfit'];H=st['H'];filt,pull,push=st['filt'],st['pull'],st['push'];OW,W=st['originalW'],st['W'];del st;full_safe=True
save('R9_protocol.json',dict(method=__doc__,channel='R',source='R4_repeatable_red',wavelengths=[18,22,28,36,44,58],seed=560913,gate=[.9,1.1],limits='Frozen red covariance, ridge and repeatability gain; same source/detector differential operator as prior G qualification. Shared calibration not eliminated.'))
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
    assert info==0;D=filt(latent);gain=np.load(OUT/'arrays/R4_repeatable_red.npz')['gain'];D=irfft2(rfft2(D)*gain,s=(N,N));correction=sum(OW[i]*pull(D,i) for i in range(len(names)))/np.maximum(oden,1e-30)
    return baseout-correction,baseout,rhsnorm
rng=np.random.default_rng(560913);rows=[];detrows=[];views={}
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
np.savez_compressed(OUT/('arrays/R9_injection_views.npz' if full_safe else 'arrays/B7_injection_views.npz'),**views)
save('R9_repeatable_injections.json' if full_safe else 'B7_global_injections.json',dict(method=__doc__,scene=rows,detector_only=detrows,all_scene_pass=all(q['pass_gate'] for q in rows),all_detector_no_amplification=all(q['no_amplification'] for q in detrows),repeatability_gain_sha256=sha(OUT/'arrays/R4_repeatable_red.npz'),covariance_sha256=sha(OLD/'arrays/B3_R67_robust_hetero_full_safe_variance_field.npy'),model_script_sha256=sha(ROOT/'research/tools/earthshine_max_detail_20260913/b3_fpn_full.py'),full_safe=full_safe,limits=['Differential operator on calibrated registered G, not a new absolute RAW-to-display test','Covariance and ridge frozen; detector perturbations do not retrain stochastic error estimates','Scene injection passes in a free-scene model by construction; detector-only controls and external comparison remain essential']))
