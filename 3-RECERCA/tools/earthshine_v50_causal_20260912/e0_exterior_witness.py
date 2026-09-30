"""Additive exterior-only empirical transfer, disjoint from lunar target photons.
Each native field is centred by a deep-only plane BEFORE a frozen exterior
window. Gaussian predictors use opposite green photons, zero lunar interior,
no mask normalization and no inverse/core gain. Fixed cell/nuisance projection.
A source-level empirical witness, not an identified physical PSF.
"""
from common50 import *
from scipy.fft import dctn,idctn
from scipy.ndimage import map_coordinates
from scipy.optimize import nnls
from scipy.linalg import cho_factor,cho_solve
import gc,time
SIG=np.array([1.,2.,4.,8.,16.,32.,64.]);metadata={r['stem']:r for r in json.loads((NATIVE/'D1_inputs.json').read_text())['frames']};frames=json.loads((ROOT/'output/earthshine_diffraction_20260912/A2_stack_plan.json').read_text())['frames'];edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
plan=dict(method=__doc__,sigmas=SIG.tolist(),exterior_window='Frozen smoothstep distance+2..+4px from inherited F4; predictor source only, NOT new lunar alpha or boundary.',training=[r['stem'] for r in frames if metadata[r['stem']]['role']=='training'],reserved=[r['stem'] for r in frames if metadata[r['stem']]['role']!='training'],target_fit='r260..449 andd<=-6, native5pxcells, parities separate',operator='Unnormalized convolution; zero interior and double opposite-green density; DCT even extension; native sigma_world/sqrt2',controls='Actual90degree rotation about worldMooncentre of donor-predictor; null independently fitted. Full source-unit residuals, no1/(1−P). Before any photo: cutoff sensitivity, heldout frames, independent Sony, injection andcensoredlong completion.',limits='Shared calibration/FPN, empiricalpositivebasisnotPSF, commonstaticcomponent stillconditional. No outputcorrection accepted from temporalfit alone.')
save('E0_plan.json',plan);records=[]
for meta in frames:
 stem=meta['stem'];t0=time.time();z=np.load(NATIVE/f'D0_native_field_{stem}.npz');g=z['g'].astype(float);assert np.all(z['valid']);vv,uu=np.mgrid[:g.shape[0],:g.shape[1]];u=uu+int(z['u0']);v=vv+int(z['v0']);nx=1+u+v;ny=u-v;J=z['native_to_world'];origin=z['world_origin'];x=origin[0]+J[0,0]*nx+J[0,1]*ny;y=origin[1]+J[1,0]*nx+J[1,1]*ny;r=np.hypot(x-CX,y-CY);a=np.arctan2(y-CY,x-CX)%(2*np.pi);d=r-np.interp(a,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi)
 deep=r<350;XX=(x-CX)/455;YY=(y-CY)/455;A=np.c_[np.ones(deep.sum()),XX[deep],YY[deep]];b=np.linalg.lstsq(A,g[deep],rcond=None)[0];contrast=g-b[0]-b[1]*XX-b[2]*YY;tt=np.clip((d-2)/2,0,1);O=tt*tt*(3-2*tt);donor=contrast*O;parity=nx%2
 use=(r>=260)&(r<458)&(x>=0)&(x<N)&(y>=0)&(y<N);cell=np.floor(y[use]/STEP).astype(int)*NC+np.floor(x[use]/STEP).astype(int);ids=2*cell+parity[use];unique,index,count=np.unique(ids,return_inverse=True,return_counts=True);good=count>=3;look=np.full(len(unique),-1);look[good]=np.arange(good.sum());keep=good[index];take=np.flatnonzero(use)[keep];index=look[index[keep]];count=count[good];unique=unique[good];nr=len(count)
 def reduce(a):return np.bincount(index,weights=a.ravel()[take],minlength=nr)/count
 val=reduce(g);var=np.bincount(index,weights=z['variance'].ravel()[take],minlength=nr)/count**2;gx=reduce(x);gy=reduce(y);radius=np.hypot(gx-CX,gy-CY);angle=np.arctan2(gy-CY,gx-CX)%(2*np.pi);dist=reduce(d);rowspar=unique%2
 obs=dict(cell=unique//2,parity=rowspar,g=val,variance=var,x=gx,y=gy,radius=radius,angle=angle,distance=dist,fit=(radius<449)&(dist<=-6));old=np.load(PRIOR/f'A1_observations_{stem}.npz');assert all(np.array_equal(obs[k],old[k]) for k in obs)
 # Rotate requested feature locations in the world grid, then invert native map.
 xp=CX-(y.ravel()[take]-CY);yp=CY+(x.ravel()[take]-CX);native=np.c_[xp-origin[0],yp-origin[1]]@np.linalg.inv(J).T;ru=(native[:,0]+native[:,1]-1)/2-int(z['u0']);rv=(native[:,0]-native[:,1]-1)/2-int(z['v0']);assert min(ru.min(),rv.min())>=0 and ru.max()<g.shape[1]-1 and rv.max()<g.shape[0]-1
 freq=(np.arange(g.shape[0])/(2*g.shape[0]))[:,None]**2+(np.arange(g.shape[1])/(2*g.shape[1]))[None,:]**2;features=np.zeros((nr,len(SIG)));rotated=features.copy()
 for p in [0,1]:
  F=dctn(2*np.where(parity!=p,donor,0),type=2,norm='ortho')
  for k,sigma in enumerate(SIG):
   smooth=idctn(F*np.exp(-np.pi**2*sigma*sigma*freq),type=2,norm='ortho');red=reduce(smooth);features[rowspar==p,k]=red[rowspar==p];rot=map_coordinates(smooth,[rv,ru],order=1,mode='nearest');rr=np.bincount(index,weights=rot,minlength=nr)/count;rotated[rowspar==p,k]=rr[rowspar==p]
 np.savez_compressed(OUT/f'E0_features_{stem}.npz',**obs,features=features,rotated=rotated,deep_plane=b,sigma=SIG)
 records.append(dict(stem=stem,role=metadata[stem]['role'],epoch=metadata[stem]['epoch'],deep_plane=b.tolist(),rows=nr,seconds=time.time()-t0));save('E0_inputs.json',dict(plan=plan,frames=records));print(stem,'DONE',round(time.time()-t0,2),flush=True);del z,g,features,rotated;gc.collect()
# Weighted fixed-effect projection: common lunar cell and per-frame plane.
data={r['stem']:dict(np.load(OUT/f'E0_features_{r["stem"]}.npz')) for r in frames};training=[data[s] for s in plan['training']];cells=np.unique(np.concatenate([r['cell'][r['fit']] for r in training]));lookup=np.full(NC*NC,-1);lookup[cells]=np.arange(len(cells));nc=len(cells);pc=3*(len(training)-1);ii=[];yy=[];ww=[];PP=[];FF=[];RR=[]
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
  pred=r['features' if key=='real' else 'rotated']@p;np.savez_compressed(OUT/f'E1_{key}_{s}.npz',scatter=pred,corrected=r['g']-pred)
 print('FIT',key,reports[key],flush=True)
save('E1_fit.json',dict(plan=plan,models=reports,warning='Conditional empirical transfer; no PSF claim, no source photos or revised alpha. Raw observations unchanged.'))
