"""Windowed source pilot: simultaneous scene and moving detector field.
Ridge regularizes detector terms only, preserving a shared injected scene.
Selection is internal training leave-one-out, then untouched temporal test.
"""
from common import *
from scipy.fft import rfft2,irfft2
from scipy.signal.windows import tukey
from spectral import fft_stats
claim();design=json.loads((OUT/'B0_fpn_design.json').read_text());plan=json.loads((OUT/'PLAN.json').read_text());names=design['names'];sh=np.array(design['shifts_common']);n=512;x0,y0,x1,y1=design['pilot']['box'];sl=np.s_[y0:y1,x0:x1];r,t=geometry();r=r[sl]
y,x=np.mgrid[:n,:n]/n*2-1;basis=np.stack([x**i*y**j for i in range(4) for j in range(4-i)],-1);win=tukey(n,.5)[:,None]*tukey(n,.5)[None,:];bw=basis.reshape(-1,10)*win.ravel()[:,None]
def encode(a):
    c=np.linalg.lstsq(bw,a.ravel()*win.ravel(),rcond=None)[0]
    return rfft2((a-basis@c)*win)
def gm(z):return (z['G1']*z['G1_q']+z['G2']*z['G2_q'])/np.maximum(z['G1_q']+z['G2_q'],1e-30)
Y=[];exp=[];weights=[]
for stem in names:
    z=np.load(OUT/'native'/('vixen_'+stem+'.npz'));a=gm(z)[sl];assert np.isfinite(a).all();Y.append(encode(a));m=next(m for m in frames() if m['stem']==stem);exp.append(m['exp'])
    vv=np.median((z['G1_var'][sl]+z['G2_var'][sl])/4);weights.append(1/vv)
Y=np.array(Y);exp=np.array(exp);weights=np.array(weights);weights/=weights.sum();train=np.array([s in plan['pilot']['fit_vixen'] for s in names]);test=~train
fy=np.fft.fftfreq(n)[:,None];fx=np.fft.rfftfreq(n)[None,:];freq=np.hypot(fx,fy);band=(freq>=1/64)&(freq<=1/16);kidx=np.flatnonzero(band.ravel());YY=Y.reshape(len(names),-1)[:,kidx]
def makeX(shifts,kind):
    phase=np.exp(2j*np.pi*(shifts[:,0,None,None]*fx+shifts[:,1,None,None]*fy)).reshape(len(names),-1)[:,kidx]
    aa=1/exp;aa/=np.sqrt(np.sum(weights[train]*aa[train]**2)/weights[train].sum())
    cols=[np.ones_like(phase)]
    if kind in ['fixed','both']:cols.append(phase)
    if kind in ['dark','both']:cols.append(phase*aa[:,None])
    return np.stack(cols,-1)
def fit_predict(y,X,idx,lam):
    xx=X[idx];w=weights[idx]/weights[idx].sum();normal=np.einsum('ifc,ifd,i->fcd',xx.conj(),xx,w);rhs=np.einsum('ifc,if,i->fc',xx.conj(),y[idx],w)
    for k in range(1,X.shape[-1]):normal[:,k,k]+=lam
    coef=np.linalg.solve(normal,rhs[...,None])[...,0];pred=np.einsum('ifc,fc->if',X,coef)
    return coef,pred
def loss(a,b,idx):return float(np.sum(weights[idx,None]*abs(a[idx]-b[idx])**2)/weights[idx].sum()/a.shape[1])
cv=[]
for kind in ['fixed','dark','both']:
    X=makeX(sh,kind)
    for lam in [.1,1.,10.]:
        ls=[]
        for i in np.flatnonzero(train):
            idx=train.copy();idx[i]=False;co,pr=fit_predict(YY,X,idx,lam);ls.append(float(np.mean(abs(pr[i]-YY[i])**2)))
        cv.append(dict(kind=kind,ridge=lam,cv_loss=float(np.average(ls,weights=weights[train])),loss_per_train_frame=ls))
best=min(cv,key=lambda a:a['cv_loss']);save('B1_model_selected.json',dict(selected=best,training_CV=cv,selection='Training frames only, 16-64px fixed; BEFORE reserved data errors or Sony analysis'))
X=makeX(sh,best['kind']);coef,pred=fit_predict(YY,X,train,best['ridge']);base=np.average(YY[train],weights=weights[train],axis=0);basepred=np.broadcast_to(base,YY.shape)
rng=np.random.default_rng(551310);perm=rng.permutation(len(names));nullcoef,nullpred=fit_predict(YY,makeX(sh[perm],best['kind']),train,best['ridge'])
testloss=loss(YY,pred,test);baseloss=loss(YY,basepred,test);nullloss=loss(YY,nullpred,test)
scene=Y[train].mean(0).copy();scene.ravel()[kidx]=coef[:,0];baseline=Y[train].mean(0).copy();baseline.ravel()[kidx]=base
full=irfft2(scene-baseline,s=(n,n));delta=np.divide(full,win,out=np.zeros_like(full),where=win>.2)
np.savez_compressed(OUT/'arrays/B1_fpn_pilot.npz',baseline=baseline,scene=scene,delta=delta,window=win,scene_coeff=coef[:,0],detector_coeff=coef[:,1:],freq_indices=kidx,raw_fft=Y)
# Scene and detector injections through the identical spatial window, carrying
# the actual measured displacements. Spatial injection avoids a tautological
# same-Fourier-matrix test only. Evaluation uses central window=1 region.
inj=[]
for j in range(8):
    wl=rng.uniform(18,60);ang=rng.uniform(0,2*np.pi);phase=rng.uniform(0,2*np.pi);kx,ky=np.cos(ang)/wl,np.sin(ang)/wl
    px,py=np.meshgrid(np.arange(n),np.arange(n));s=np.sin(2*np.pi*(kx*px+ky*py)+phase)
    det=np.array([np.sin(2*np.pi*(kx*(px+dx)+ky*(py+dy))+phase+1.1) for dx,dy in sh])
    sy=np.array([encode(s) for _ in names]).reshape(len(names),-1)[:,kidx]
    dy=np.array([encode(d) for d in det]).reshape(len(names),-1)[:,kidx]
    ci,pi=fit_predict(YY+sy,X,train,best['ridge']);target=encode(s).ravel()[kidx];rec=ci[:,0]-coef[:,0];tr=float(np.vdot(target,rec).real/np.vdot(target,target).real)
    cd,pd=fit_predict(YY+dy,X,train,best['ridge']);leak=cd[:,0]-coef[:,0];unsub=np.average(dy[train],weights=weights[train],axis=0)
    inj.append(dict(index=j,wavelength=wl,angle=ang,scene_transfer=tr,scene_pass=.9<=tr<=1.1,detector_residual_ratio=float(np.linalg.norm(leak)/np.linalg.norm(unsub))))
rep=dict(method=__doc__,selected=best,heldout_loss=dict(baseline=baseloss,model=testloss,null_permuted_pose=nullloss,improvement_pct=100*(1-testloss/baseloss),true_pose_better_than_null=testloss<nullloss),injections=inj,frame_names=names,train=train,test=test,scope='512px central source patch; no photographic product, exterior or whole-disc correction',limitations=['FPN stationary model competes with changing scattered light and seeing','Windowing breaks exact translation model at support boundary; injection measures this approximation','A pass of common scene injection alone is not proof of defect recovery'])
save('B1_fpn_pilot.json',rep);print('FPN',rep['heldout_loss'],'SELECTED',best,'INJ',[(round(q['scene_transfer'],3),round(q['detector_residual_ratio'],3)) for q in inj],flush=True)
