"""Fit a positive multiscale scattering mixture by exact spectral forward terms.

Each target green measurement uses ONLY opposite green photons in its smooth
scatter predictor. A common latent lunar cell and per-frame plane absorb lunar
structure/offsets; they are eliminated analytically. Unlike the prior frozen
12/4-px cascade, the wings are fitted jointly, using the lunar face and actual
time-varying observed exterior, not a linear exterior profile or static scene.
No output pixels or photographic correction are published by this diagnostic.
"""
from common50 import *
from scipy.fft import dctn,idctn
from scipy.optimize import minimize
from scipy.linalg import cho_factor,cho_solve
import time

metadata={r['stem']:r for r in json.loads((NATIVE/'D1_inputs.json').read_text())['frames']}
frames=json.loads((ROOT/'output/earthshine_diffraction_20260912/A2_stack_plan.json').read_text())['frames']
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
save('A1_plan.json',dict(method=__doc__,sigma_world_pixels=SIGMA.tolist(),weights='Nonnegative; total scattering <=0.30; direct core weight 1-sum(p). Exact inverse transfer in predictor, no truncated Neumann expansion.',training=[r['stem'] for r in frames if metadata[r['stem']]['role']=='training'],validation_frames=[r['stem'] for r in frames if metadata[r['stem']]['role']!='training'],parameter_support='Measured native cell radius260..449 and distance<=-6 from observed edge; complete uncensored fields only. Final assessment also reports -6..-0.5 separately, not used for parameter fitting.',sampling='5x5 presentation-grid cells, green parities separate; no resampling of measured radiance',operator='DCT even extension; Gaussian world sigma/sqrt2 native. Target is measured green; scatter is computed from opposite raw green plane. No static exterior across frames.',validation='Compare heldout epochs/sectors to uncorrected source and fixed 90-degree predictor control. Require improved independent consistency, no new ring/texture loss and source injection before photographic promotion. No automatic acceptance from training objective.',limits=['Calibration and registration remain inherited and shared','Positive Gaussian mixture is a conditional scatter model, not a unique instrument PSF','The cross-telescope judge and final Camera Raw/native Photoshop checks remain mandatory','Only fully uncensored fields identify the kernel; censored captures need a separately qualified predictor before reuse']))

def load_frame(meta):
    stem=meta['stem'];z=np.load(NATIVE/f'D0_native_field_{stem}.npz');g=z['g'];assert np.all(z['valid'])
    vv,uu=np.mgrid[:g.shape[0],:g.shape[1]];u=uu+int(z['u0']);v=vv+int(z['v0']);nx=1+u+v;ny=u-v
    J=z['native_to_world'];origin=z['world_origin'];x=origin[0]+J[0,0]*nx+J[0,1]*ny;y=origin[1]+J[1,0]*nx+J[1,1]*ny
    r=np.hypot(x-CX,y-CY);a=np.arctan2(y-CY,x-CX)%(2*np.pi);d=r-np.interp(a,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi)
    use=(r>=260)&(r<458)&(x>=0)&(x<N)&(y>=0)&(y<N)
    parity=nx%2;cell=np.floor(y[use]/STEP).astype(int)*NC+np.floor(x[use]/STEP).astype(int)
    ids=2*cell+parity[use];unique,index,count=np.unique(ids,return_inverse=True,return_counts=True)
    good=count>=3;lookup=np.full(len(unique),-1);lookup[good]=np.arange(good.sum());keep=good[index]
    take=np.flatnonzero(use)[keep];index=lookup[index[keep]];count=count[good];unique=unique[good];nr=len(count)
    def reduce(a):return np.bincount(index,weights=a.ravel()[take],minlength=nr)/count
    val=reduce(g);var=np.bincount(index,weights=z['variance'].ravel()[take],minlength=nr)/count**2
    gx=reduce(x);gy=reduce(y);radius=np.hypot(gx-CX,gy-CY);angle=np.arctan2(gy-CY,gx-CX)%(2*np.pi);dist=reduce(d)
    freq=(np.arange(g.shape[0])/(2*g.shape[0]))[:,None]**2+(np.arange(g.shape[1])/(2*g.shape[1]))[None,:]**2
    E=np.exp(-np.pi**2*SIGMA[:,None,None]**2*freq).astype(np.float64)
    # Gaussian exp(-2*pi²*sigma_native²*f²), sigma_native=sigma_world/sqrt2.
    F=[dctn(2*np.where(parity!=p,g,0),type=2,norm='ortho') for p in [0,1]]
    rows=unique%2;result=dict(stem=stem,role=metadata[stem]['role'],epoch=metadata[stem]['epoch'],shape=g.shape,E=E,F=F,take=take,index=index,count=count,parity=rows,cell=unique//2,g=val,variance=var,x=gx,y=gy,radius=radius,angle=angle,distance=dist,fit=(radius<449)&(dist<=-6))
    np.savez_compressed(OUT/f'A1_observations_{stem}.npz',**{k:result[k] for k in ['cell','parity','g','variance','x','y','radius','angle','distance','fit']})
    print('LOADED',stem,len(val),'cells',flush=True);return result

def predictor(frame,p,jac=False,rotated=False):
    E=frame['E'];S=np.tensordot(p,E,axes=1);T=1-p.sum()+S;fil=S/T
    transfer=[fil]+[(E[k]*(1-p.sum())+S)/T**2 for k in range(len(p))] if jac else [fil]
    outputs=[]
    for transfer_k in transfer:
        val=np.zeros(len(frame['g']))
        for parity in [0,1]:
            a=idctn(frame['F'][parity]*transfer_k,type=2,norm='ortho')
            reduced=np.bincount(frame['index'],weights=a.ravel()[frame['take']],minlength=len(val))/frame['count']
            val[frame['parity']==parity]=reduced[frame['parity']==parity]
        outputs.append(val)
    return np.stack(outputs,axis=1)

training=[load_frame(r) for r in frames if metadata[r['stem']]['role']=='training']
cells=np.unique(np.concatenate([r['cell'][r['fit']] for r in training]));lookup=np.full(NC*NC,-1);lookup[cells]=np.arange(len(cells));nc=len(cells);pc=3*(len(training)-1)
indices=[];ys=[];ws=[];ps=[];segments=[];start=0
for j,r in enumerate(training):
    use=r['fit'];nr=int(use.sum());idx=lookup[r['cell'][use]];P=np.zeros((nr,pc))
    if j:P[:,3*(j-1):3*j]=np.stack([np.ones(nr),(r['x'][use]-CX)/455,(r['y'][use]-CY)/455],axis=1)
    indices.append(idx);ys.append(r['g'][use]);ws.append(1/np.maximum(r['variance'][use]*14.826313721285086,1e-9));ps.append(P);segments.append(slice(start,start+nr));start+=nr
i=np.concatenate(indices);y=np.concatenate(ys);w=np.concatenate(ws);P=np.concatenate(ps);D=np.bincount(i,weights=w,minlength=nc);safe=np.maximum(D,1e-30)
B=np.stack([np.bincount(i,weights=w*P[:,j],minlength=nc) for j in range(pc)],axis=1)
H=P.T@(w[:,None]*P)-B.T@(B/safe[:,None]);chol=cho_factor(H)
def project(v):
    b=np.bincount(i,weights=w*v,minlength=nc);planes=cho_solve(chol,P.T@(w*v)-B.T@(b/safe));m=(b-B@planes)/safe
    return m[i]+P@planes,m,planes
yr=y-project(y)[0];baseline=float(w@yr**2);history=[];last={}
def objective(p):
    t0=time.time();parts=[predictor(r,p,True)[r['fit']] for r in training];c=np.concatenate([a[:,0] for a in parts]);J=np.concatenate([a[:,1:] for a in parts]);v=y-c;pred,m,planes=project(v);res=v-pred
    obj=float(w@res**2)/baseline;grad=-2*J.T@(w*res)/baseline
    last.update(p=p.copy(),c=c,J=J,res=res,m=m,planes=planes)
    history.append(dict(p=p.tolist(),relative_objective=obj,seconds=time.time()-t0));save('A1_fit_progress.json',dict(history=history))
    print('FIT',np.round(p,6),round(obj,6),round(time.time()-t0,2),'s',flush=True)
    return obj,grad
opt=minimize(objective,np.array([.005,.01,.007,.007,.003]),jac=True,method='SLSQP',bounds=[(0,.2)]*5,constraints=[dict(type='ineq',fun=lambda p:.3-p.sum(),jac=lambda p:-np.ones(5))],options=dict(maxiter=35,ftol=1e-9,disp=True))
objective(opt.x);p=opt.x;np.savez_compressed(OUT/'A1_fitted_model.npz',p=p,sigma=SIGMA,cells=cells,latent_scaled=last['m'],planes=last['planes'])
rows=[]
for r in training:
    c=predictor(r,p)[:,0];np.savez_compressed(OUT/f'A1_corrected_cells_{r["stem"]}.npz',scatter=c,corrected=(r['g']-c)/(1-p.sum()))
    rows.append(dict(stem=r['stem'],epoch=r['epoch'],role=r['role']))
save('A1_fit.json',dict(method=__doc__,success=bool(opt.success),message=str(opt.message),p=p.tolist(),sigma=SIGMA.tolist(),total_scatter=float(p.sum()),training_relative_objective=float(opt.fun),at_bounds=[bool(q<1e-6 or q>.199999) for q in p],history=history,training=rows,publication='NONE; reserved epochs/independent telescope/injection not yet checked'))
print('FIT COMPLETE',p,opt.fun,flush=True)
# Save heldout predictions with the FROZEN fitted kernel; no fit to their halo.
training.clear()
import gc;gc.collect()
for meta in frames:
    if metadata[meta['stem']]['role']=='training':continue
    r=load_frame(meta);c=predictor(r,p)[:,0]
    np.savez_compressed(OUT/f'A1_corrected_cells_{r["stem"]}.npz',scatter=c,corrected=(r['g']-c)/(1-p.sum()))
    print('RESERVED',r['stem'],'DONE',flush=True);del r;gc.collect()
print('ALL PREDICTIONS COMPLETE',flush=True)
