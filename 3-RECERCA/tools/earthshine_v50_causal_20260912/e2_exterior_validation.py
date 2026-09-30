"""Frozen exterior-predictor epoch validation in common source radiance units.
No core gain, same nuisance freedoms; real and separately trained rotated null.
Cells near boundary can span the donor cutoff and are reported separately.
"""
from common50 import *
from scipy.linalg import cho_factor,cho_solve
fit=json.loads((OUT/'E1_fit.json').read_text());plan=fit['plan'];meta={r['stem']:r for r in json.loads((NATIVE/'D1_inputs.json').read_text())['frames']};data={s:dict(np.load(OUT/f'E0_features_{s}.npz')) for s in plan['training']+plan['reserved']};training=[data[s] for s in plan['training']]
cells=np.unique(np.concatenate([z['cell'] for z in training]));nc=len(cells);lookup=np.full(NC*NC,-1);lookup[cells]=np.arange(nc);pc=3*(len(training)-1);ii=[];yy=[];ww=[];PP=[];ss={k:[] for k in ['real','rotated']}
for j,s in enumerate(plan['training']):
 z=data[s];nr=len(z['g']);P=np.zeros((nr,pc))
 if j:P[:,3*(j-1):3*j]=np.c_[np.ones(nr),(z['x']-CX)/455,(z['y']-CY)/455]
 ii.append(lookup[z['cell']]);yy.append(z['g']);ww.append(1/(14.826313721285086*z['variance']));PP.append(P)
 for key in ss:ss[key].append(np.load(OUT/f'E1_{key}_{s}.npz')['scatter'])
i=np.concatenate(ii);y=np.concatenate(yy);w=np.concatenate(ww);P=np.concatenate(PP);D=np.bincount(i,weights=w,minlength=nc);safe=np.maximum(D,1e-30);B=np.stack([np.bincount(i,weights=w*P[:,j],minlength=nc) for j in range(pc)],1);H=P.T@(w[:,None]*P)-B.T@(B/safe[:,None]);chol=cho_factor(H)
def template(y):
 b=np.bincount(i,weights=w*y,minlength=nc);planes=cho_solve(chol,P.T@(w*y)-B.T@(b/safe));return (b-B@planes)/safe
models={'baseline':template(y)}
for key in ss:models[key]=template(y-np.concatenate(ss[key]))
np.savez_compressed(OUT/'E2_templates.npz',cells=cells,**models);results=[];sectors=[]
for s in plan['reserved']:
 z=data[s];idx=lookup[z['cell']];valid=idx>=0;cal=valid&(z['radius']>=260)&(z['radius']<350);P=np.c_[np.ones(len(idx)),(z['x']-CX)/455,(z['y']-CY)/455];weight=np.zeros(len(idx));weight[valid]=1/(14.826313721285086*z['variance'][valid]+1/D[idx[valid]]);residuals={};planes={}
 for key,m in models.items():
  pred=m[np.maximum(idx,0)].copy()
  if key!='baseline':pred+=np.load(OUT/f'E1_{key}_{s}.npz')['scatter']
  plane=np.linalg.lstsq(P[cal]*np.sqrt(weight[cal,None]),(z['g']-pred)[cal]*np.sqrt(weight[cal]),rcond=None)[0];pred+=P@plane;residuals[key]=z['g']-pred;planes[key]=plane.tolist()
 reg=[]
 for label,band in [('face',(z['radius']>=350)&(z['radius']<415)),('wide_limb',(z['distance']>=-40)&(z['distance']<-6)),('last_six',(z['distance']>=-6)&(z['distance']<-.5)),('last_disjoint_guard',(z['distance']>=-6)&(z['distance']<-2))]:
  band&=valid
  for sec in range(12):
   use=band&(np.floor(z['angle']/(np.pi/6)).astype(int)==sec)
   if not use.any():continue
   sectors.append(dict(stem=s,epoch=meta[s]['epoch'],region=label,sector=sec,rows=int(use.sum()),weight=float(weight[use].sum()),sse={k:float(np.sum(weight[use]*v[use]**2)) for k,v in residuals.items()},bias_sum={k:float(np.sum(weight[use]*v[use])) for k,v in residuals.items()}))
 np.savez_compressed(OUT/f'E2_reserved_{s}.npz',**residuals,radius=z['radius'],distance=z['distance'],angle=z['angle'],weight=weight,cell=z['cell']);results.append(dict(stem=s,planes=planes))
epochs=[]
for epoch in sorted(set(r['epoch'] for r in sectors)):
 for region in ['face','wide_limb','last_six','last_disjoint_guard']:
  rr=[r for r in sectors if r['epoch']==epoch and r['region']==region];ws=sum(r['weight'] for r in rr);sse={k:sum(r['sse'][k] for r in rr) for k in models};bias={k:sum(r['bias_sum'][k] for r in rr)/ws for k in models};epochs.append(dict(epoch=epoch,region=region,mse_G2={k:v/ws for k,v in sse.items()},ratio={k:sse[k]/sse['baseline'] for k in ['real','rotated']},bias_G=bias))
save('E2_validation.json',dict(method=__doc__,epochs=epochs,frames=results,sectors=sectors,source_unit_gain=1,scope='Conditional heldout temporal prediction, not PSF or full-limb recovery'))
print(json.dumps(epochs,indent=2),flush=True)
