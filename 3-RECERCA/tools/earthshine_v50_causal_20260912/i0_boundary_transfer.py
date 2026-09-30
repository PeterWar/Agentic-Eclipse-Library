"""Boundary-constrained empirical exterior transfer, strict photon support.
The earlier G pilot extrapolated narrow kernels into an untrained edge band.
This hypothesis instead fits the observed lunar-side edge in five frames and
reserves sixteen complete frames. Both donor and target support are disjoint.
Empirical coefficients are not called PSF energy; no arbitrary mass bound.
"""
from common50 import *
from scipy.optimize import nnls
from scipy.linalg import cho_factor,cho_solve
SIG=np.array([1.,2.,4.,8.,16.,32.,64.])
frames=json.loads((ROOT/'output/earthshine_diffraction_20260912/A2_stack_plan.json').read_text())['frames']
plan=json.loads((OUT/'G0_plan.json').read_text());plan.update(method=__doc__,target_fit='r260..458; every target nativepixel d<−0.5, donor overlap exactly zero; same five training frames, sixteen heldout complete frames')
# Weighted fixed-effect projection: common lunar cell and per-frame plane.
data={r['stem']:dict(np.load(OUT/f'G0_features_{r["stem"]}.npz')) for r in frames}
for r in data.values():r['fit']=(r['distance']<-.5)&(r['max_native_distance']<-.5)&(r['donor_overlap_fraction']==0)
training=[data[s] for s in plan['training']];cells=np.unique(np.concatenate([r['cell'][r['fit']] for r in training]));lookup=np.full(NC*NC,-1);lookup[cells]=np.arange(len(cells));nc=len(cells);pc=3*(len(training)-1);ii=[];yy=[];ww=[];PP=[];FF=[];RR=[]
for j,r in enumerate(training):
 use=r['fit'];nr=int(use.sum());P=np.zeros((nr,pc))
 if j:P[:,3*(j-1):3*j]=np.c_[np.ones(nr),(r['x'][use]-CX)/455,(r['y'][use]-CY)/455]
 ii.append(lookup[r['cell'][use]]);yy.append(r['g'][use]);ww.append(1/(r['variance'][use]*14.826313721285086));PP.append(P);FF.append(r['features'][use]);RR.append(r['rotated'][use])
i=np.concatenate(ii);y=np.concatenate(yy);w=np.concatenate(ww);P=np.concatenate(PP);D=np.bincount(i,weights=w,minlength=nc);safe=np.maximum(D,1e-30);B=np.stack([np.bincount(i,weights=w*P[:,j],minlength=nc) for j in range(pc)],1);H=P.T@(w[:,None]*P)-B.T@(B/safe[:,None]);chol=cho_factor(H)
def project(v):
 b=np.bincount(i,weights=w*v,minlength=nc);planes=cho_solve(chol,P.T@(w*v)-B.T@(b/safe));m=(b-B@planes)/safe;return m[i]+P@planes
yr=y-project(y);baseline=float(w@yr**2);reports={}
for key,F in [('real',np.concatenate(FF)),('rotated',np.concatenate(RR))]:
 R=F-np.stack([project(F[:,j]) for j in range(F.shape[1])],1);norm=np.sqrt(np.sum(w[:,None]*R*R,axis=0));J=R*np.sqrt(w[:,None])/norm;coef,_=nnls(J,yr*np.sqrt(w),maxiter=1000);p=coef/norm;res=yr-R@p;sv=np.linalg.svd(J,compute_uv=False);cov=np.linalg.pinv(R.T@(w[:,None]*R));se=np.sqrt(np.diag(cov))*np.sqrt((w@res**2)/max(len(y)-nc-pc-len(SIG),1));reports[key]=dict(p=p.tolist(),train_mse_ratio=float(w@res**2)/baseline,normal_singular_values=sv.tolist(),unconstrained_conditional_SE=se.tolist(),covariance=cov.tolist(),active=int((p>1e-8).sum()))
 for s,r in data.items():
  pred=r['features' if key=='real' else 'rotated']@p;np.savez_compressed(OUT/f'I1_{key}_{s}.npz',scatter=pred,corrected=r['g']-pred)
 print('FIT',key,reports[key],flush=True)
save('I1_fit.json',dict(plan=plan,models=reports,warning='Conditional empirical transfer; no PSF claim, no source photos or revised alpha. Raw observations unchanged.'))
