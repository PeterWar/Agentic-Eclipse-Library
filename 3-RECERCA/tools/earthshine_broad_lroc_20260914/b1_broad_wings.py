"""Reproduce bounded temporal identifiability pilot; no photographic output.
Source donor centering inherits G0 (r<350, includes part of mark). Only final
coefficient fit excludes mark+guard. Report this limitation; no validation PASS.
"""
import numpy as np,json,time
from pathlib import Path
from scipy.ndimage import map_coordinates
from scipy.fft import dctn,idctn
from scipy.special import ndtr
from scipy.linalg import cho_factor,cho_solve
from scipy.optimize import nnls
R=Path.cwd();OLD=R/'output/earthshine_v50_causal_20260912';N=R/'output/earthshine_intermediate_witness_20260911';OUT=R/'output/earthshine_broad_lroc_20260914'
plan=json.loads((OLD/'I1_fit.json').read_text())['plan'];metadata={r['stem']:r for r in json.loads((N/'D1_inputs.json').read_text())['frames']}
stems=plan['training']+plan['reserved'];edge=np.load(R/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');CX=699.568111973117;CY=699.6475341408573;NC=280;STEP=5;SIG=[64.,128.,256.];data={};fields=[]
for stem in stems:
 t=time.time();z=np.load(N/f'D0_native_field_{stem}.npz');g=z['g'].astype(float);assert np.all(z['valid']);vv,uu=np.mgrid[:g.shape[0],:g.shape[1]];u=uu+int(z['u0']);v=vv+int(z['v0']);nx=1+u+v;ny=u-v;J=z['native_to_world'];origin=z['world_origin'];x=origin[0]+J[0,0]*nx+J[0,1]*ny;y=origin[1]+J[1,0]*nx+J[1,1]*ny;r=np.hypot(x-CX,y-CY);a=np.arctan2(y-CY,x-CX)%(2*np.pi);d=r-np.interp(a,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi)
 deep=r<350;XX=(x-CX)/455;YY=(y-CY)/455;A=np.c_[np.ones(deep.sum()),XX[deep],YY[deep]];b=np.linalg.lstsq(A,g[deep],rcond=None)[0];contrast=g-b[0]-b[1]*XX-b[2]*YY;tt=np.clip(d+.5,0,1);donor=contrast*tt*tt*(3-2*tt);parity=nx%2
 use=(r>=260)&(r<458)&(x>=0)&(x<1400)&(y>=0)&(y<1400);cell=np.floor(y[use]/STEP).astype(int)*NC+np.floor(x[use]/STEP).astype(int);ids=2*cell+parity[use];unique,index,count=np.unique(ids,return_inverse=True,return_counts=True);good=count>=3;look=np.full(len(unique),-1);look[good]=np.arange(good.sum());keep=good[index];take=np.flatnonzero(use)[keep];index=look[index[keep]];count=count[good];unique=unique[good];nr=len(count)
 def reduce(a):return np.bincount(index,weights=a.ravel()[take],minlength=nr)/count
 obs=dict(np.load(OLD/f'G0_features_{stem}.npz'));assert np.array_equal(obs['cell'],unique//2);assert np.max(abs(reduce(g)-obs['g']))==0;rowspar=unique%2
 xp=CX-(y.ravel()[take]-CY);yp=CY+(x.ravel()[take]-CX);native=np.c_[xp-origin[0],yp-origin[1]]@np.linalg.inv(J).T;ru=(native[:,0]+native[:,1]-1)/2-int(z['u0']);rv=(native[:,0]-native[:,1]-1)/2-int(z['v0']);freq=(np.arange(g.shape[0])/(2*g.shape[0]))[:,None]**2+(np.arange(g.shape[1])/(2*g.shape[1]))[None,:]**2;feat=np.zeros((nr,3));rot=np.zeros_like(feat)
 for p in [0,1]:
  F=dctn(2*np.where(parity!=p,donor,0),type=2,norm='ortho')
  for k,sigma in enumerate(SIG):
   smooth=idctn(F*np.exp(-2*np.pi**2*(sigma/np.sqrt(2))**2*freq),type=2,norm='ortho');red=reduce(smooth);feat[rowspar==p,k]=red[rowspar==p];rr=np.bincount(index,weights=map_coordinates(smooth,[rv,ru],order=1,mode='nearest'),minlength=nr)/count;rot[rowspar==p,k]=rr[rowspar==p]
 obs['broad']=feat;obs['null']=rot;data[stem]=obs;uu0=uu.ravel()[take];vv0=vv.ravel()[take];mass=[]
 for sig in SIG:
  sn=sig/np.sqrt(2);inside=(ndtr((g.shape[1]-.5-uu0)/sn)-ndtr((-.5-uu0)/sn))*(ndtr((g.shape[0]-.5-vv0)/sn)-ndtr((-.5-vv0)/sn));tail=np.bincount(index,weights=1-inside,minlength=nr)/count;m=(obs['radius']<390)&(obs['x']>=550)&(obs['x']<723)&(obs['y']>=902)&(obs['y']<1048);mass.append(np.percentile(tail[m],[50,100]).tolist())
 fields.append(dict(stem=stem,old_sigma64_max_error=float(abs(feat[:,0]-obs['features'][:,-1]).max()),outside_mass_by_sigma_median_max=mass));print('FIELD',stem,round(time.time()-t,2),flush=True)
def setup(selected):
 def selection(z):return (z['radius']<390)&~((z['x']>=500)&(z['x']<773)&(z['y']>=852)&(z['y']<1098))
 cells=np.unique(np.concatenate([data[s]['cell'][selection(data[s])] for s in selected]));lookup=np.full(NC*NC,-1);lookup[cells]=np.arange(len(cells));nc=len(cells);pc=3*(len(selected)-1);ii=[];yy=[];ww=[];PP=[];FF=[];RR=[]
 for j,s in enumerate(selected):
  z=data[s];use=selection(z);nr=int(use.sum());P=np.zeros((nr,pc))
  if j:P[:,3*(j-1):3*j]=np.c_[np.ones(nr),(z['x'][use]-CX)/455,(z['y'][use]-CY)/455]
  ii.append(lookup[z['cell'][use]]);yy.append(z['g'][use]);ww.append(1/(z['variance'][use]*14.826313721285086));PP.append(P);FF.append(z['broad'][use]);RR.append(z['null'][use])
 i=np.concatenate(ii);y=np.concatenate(yy);w=np.concatenate(ww);P=np.concatenate(PP);D=np.bincount(i,weights=w,minlength=nc);safe=np.maximum(D,1e-30);B=np.stack([np.bincount(i,weights=w*P[:,j],minlength=nc) for j in range(pc)],1);H=P.T@(w[:,None]*P)-B.T@(B/safe[:,None]);chol=cho_factor(H)
 def project(v):
  b=np.bincount(i,weights=w*v,minlength=nc);planes=cho_solve(chol,P.T@(w*v)-B.T@(b/safe));return ((b-B@planes)/safe)[i]+P@planes
 yr=y-project(y);baseline=float(w@yr**2);rep={}
 for name,F in [('real',np.concatenate(FF)),('rotated',np.concatenate(RR))]:
  residual=F-np.stack([project(F[:,k]) for k in range(3)],1);norm=np.sqrt(np.sum(w[:,None]*residual**2,axis=0));J=residual*np.sqrt(w[:,None])/norm;p,_=nnls(J,yr*np.sqrt(w));p/=norm;res=yr-residual@p;sv=np.linalg.svd(J,compute_uv=False);cov=np.linalg.pinv(residual.T@(w[:,None]*residual));se=np.sqrt(np.diag(cov))*np.sqrt((w@res**2)/(len(y)-nc-pc-3));uncon=np.linalg.lstsq(J,yr*np.sqrt(w),rcond=None)[0]/norm
  rep[name]=dict(p=p.tolist(),unconstrained=uncon.tolist(),se=se.tolist(),ratio=float(w@res**2)/baseline,singular=sv.tolist(),condition=float(sv[0]/sv[-1]),projection_retained_fraction=(norm/np.sqrt(np.sum(w[:,None]*F**2,axis=0))).tolist())
 return rep
results=dict(full=setup(plan['training']),epochs={})
for label,epoch in [('early','vixen_2'),('late','vixen_5')]:results['epochs'][label]=setup([s for s in plan['training'] if metadata[s]['epoch']==epoch])
results.update(sigmas=SIG,training=plan['training'],reserved=plan['reserved'],fields=fields,complete_reserved_prediction_performed=False,donor_plane_mark_excluded=False,coefficient_fit_mark_guard_excluded=True,status='NOT_IDENTIFIED_NO_CORRECTION_PROMOTED')
(OUT/'B1_broad_wings.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({k:v for k,v in results.items() if k!='fields'},indent=2),flush=True)
