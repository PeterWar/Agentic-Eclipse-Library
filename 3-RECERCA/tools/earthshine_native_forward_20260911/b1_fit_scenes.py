"""Native-CFA lunar/solar fit with fixed lambda and explicit nonnegative scenes.
Compare prescribed solar motion with a refitted static control. Four exposures
remain reserved. Positivity is a constraint in the fit, never a clipped result.
"""
from native_operator import *
from scipy.sparse import load_npz,vstack,hstack,block_diag,coo_matrix
from scipy.sparse.linalg import LinearOperator,cg
from scipy.optimize import minimize
import time,gc

geo=Geometry(16);meta=json.loads((OUT/'B0_matrices.json').read_text());rows=meta['frames'];assert len(rows)==12;train=[r for r in rows if r['train']];reserved=[r for r in rows if not r['train']];folder=OUT/'matrices';lam=PLAN['regularization_lambda_initial'];ALPHA=14.826313721285086
data={r['stem']:dict(np.load(folder/f'{r["stem"]}_observations.npz')) for r in rows}
inside=[];outside=[]
for r in train:
    z=data[r['stem']];rr=np.hypot(z['xy'][:,0]-CX,z['xy'][:,1]-CY);inside.extend(z['g'][rr<435]);outside.extend(z['g'][rr>465])
ms=float(np.median(inside));cs=float(np.median(outside));assert ms>0 and cs>0

def laplacian(indices):
    lookup=np.full(geo.size,-1,dtype=int);lookup[indices]=np.arange(len(indices));array=lookup.reshape(geo.shape);ri=[];ci=[];value=[];degree=np.zeros(len(indices))
    for aa,bb in [(array[:,:-1],array[:,1:]),(array[:-1],array[1:])]:
        good=(aa>=0)&(bb>=0);a=aa[good];b=bb[good];ri.extend([a,b]);ci.extend([b,a]);value.extend([-np.ones(len(a)),-np.ones(len(a))]);np.add.at(degree,a,1);np.add.at(degree,b,1)
    ri.append(np.arange(len(indices)));ci.append(np.arange(len(indices)));value.append(degree)
    return coo_matrix((np.concatenate(value),(np.concatenate(ri),np.concatenate(ci))),shape=(len(indices),len(indices))).tocsr()

results=[]
for mode in ['moving','static']:
    start=time.time();AM=[];AC=[];targets=[];weights=[]
    for r in train:
        stem=r['stem'];z=data[stem];AM.append(load_npz(folder/f'{stem}_lunar.npz'));AC.append(load_npz(folder/f'{stem}_solar_{mode}.npz'));targets.append(z['g']);weights.append(z['q']/(z['weight_variance']*ALPHA))
    M=vstack(AM,format='csr');C=vstack(AC,format='csr');w=np.concatenate(weights);target=np.concatenate(targets);mi=np.flatnonzero(np.asarray(M.power(2).T@w).ravel()>1e-20);ci=np.flatnonzero(np.asarray(C.power(2).T@w).ravel()>1e-20)
    A=hstack([M[:,mi]*ms,C[:,ci]*cs],format='csr').multiply(np.sqrt(w)[:,None]).tocsr();b=target*np.sqrt(w);L=block_diag([laplacian(mi),laplacian(ci)],format='csr');eps=1e-10
    diag=np.asarray(A.power(2).sum(0)).ravel()+lam*np.asarray(L.power(2).sum(0)).ravel()+eps;scale=1/np.sqrt(diag);B=A.multiply(scale[None,:]).tocsr();K=L.multiply(scale[None,:]).tocsr();rhs=B.T@b
    def normal(u):return B.T@(B@u)+lam*(K.T@(K@u))+eps*scale**2*u
    def objective(u):
        r=B@u-b;k=K@u;f=.5*np.dot(r,r)+.5*lam*np.dot(k,k)+.5*eps*np.dot(scale*u,scale*u);g=B.T@r+lam*(K.T@k)+eps*scale**2*u;return f,g
    steps=[0]
    def cb(u):
        steps[0]+=1
        if steps[0]%200==0:print(mode,'CG',steps[0],flush=True)
    op=LinearOperator((len(rhs),len(rhs)),matvec=normal,dtype=np.float64);u,info=cg(op,rhs,x0=np.ones(len(rhs))/scale,rtol=1e-9,atol=0,maxiter=4000,callback=cb)
    cg_res=normal(u)-rhs;cg_blocks={k:float(np.linalg.norm(cg_res[s])/max(np.linalg.norm(rhs[s]),1e-30)) for k,s in [('lunar',slice(None,len(mi))),('solar',slice(len(mi),None))]};unconstrained=u*scale;cg_receipt=dict(info=int(info),iterations=steps[0],block_relative_residual=cg_blocks,negative_lunar_nodes=int(np.sum(unconstrained[:len(mi)]<0)),minimum_lunar_G=float(np.min(unconstrained[:len(mi)]*ms)))
    np.savez_compressed(OUT/f'B1_{mode}_unconstrained.npz',u=u,scale=scale,mi=mi,ci=ci,ms=ms,cs=cs)
    assert info==0 and max(cg_blocks.values())<1e-6,cg_receipt
    print(mode,'UNCONSTRAINED',json.dumps(cg_receipt),flush=True)
    count=[0]
    def bounded_cb(v):
        count[0]+=1
        if count[0]%200==0:
            f,g=objective(v);pg=np.where((v<=1e-10)&(g>0),0,g);print(mode,'NONNEG',count[0],f,'pg',float(np.max(abs(pg))),flush=True)
            np.savez_compressed(OUT/f'B1_{mode}_latest.npz',u=v,scale=scale,mi=mi,ci=ci,ms=ms,cs=cs)
    opt=minimize(objective,np.maximum(u,0),method='L-BFGS-B',jac=True,bounds=[(0,None)]*len(u),callback=bounded_cb,options={'maxiter':2500,'maxcor':20,'ftol':1e-13,'gtol':1e-7,'maxls':40})
    v=opt.x*scale;f,g=objective(opt.x);pg=np.where((opt.x<=1e-10)&(g>0),0,g);kkt={key:float(np.max(abs(pg[s]))/max(np.max(abs(rhs[s])),1)) for key,s in [('lunar',slice(None,len(mi))),('solar',slice(len(mi),None))]}
    lunar=np.zeros(geo.size);solar=lunar.copy();lunar[mi]=v[:len(mi)]*ms;solar[ci]=v[len(mi):]*cs;predictions={};tests=[]
    for r in rows:
        stem=r['stem'];z=data[stem];pred=load_npz(folder/f'{stem}_lunar.npz')@lunar+load_npz(folder/f'{stem}_solar_{mode}.npz')@solar;ww=z['q']/(z['weight_variance']*ALPHA);rr=np.hypot(z['xy'][:,0]-CX,z['xy'][:,1]-CY);regions=[]
        for lo,hi in [(415,435),(435,445),(445,449),(449,454),(454,480),(480,500)]:
            mask=(rr>=lo)&(rr<hi)
            if mask.sum()<20:continue
            residual=pred[mask]-z['g'][mask];regions.append(dict(radius=[lo,hi],samples=int(mask.sum()),weighted_mean_square=float(np.mean(ww[mask]*residual**2)),median_residual_G=float(np.median(residual)),rms_residual_G=float(np.sqrt(np.mean(residual**2))),weighted_residual_quantiles=np.percentile(ww[mask]*residual**2,[50,90,99]).tolist()))
        tests.append(dict(stem=stem,exp=r['exp'],reserved=not r['train'],regions=regions));predictions[stem]=pred
    shape=geo.shape;ny,nx=shape;y,x=np.mgrid[:ny,:nx];x=x+geo.box[0];y=y+geo.box[1];rr=np.hypot(x-CX,y-CY);observed=(x>=1117)&(x<=1187)&(y>=630)&(y<=770);inside=(x<geo.border(y));mask=np.zeros(geo.size,dtype=bool);mask[mi]=True;mask=mask.reshape(shape)&inside&observed;statistics=[]
    for lo,hi in [(415,435),(435,445),(445,449),(449,454)]:
        use=mask&(rr>=lo)&(rr<hi)
        if use.sum():statistics.append(dict(radius=[lo,hi],nodes=int(use.sum()),at_zero=int(np.sum(lunar.reshape(shape)[use]<=1e-6)),radiance_quantiles=np.percentile(lunar.reshape(shape)[use],[0,1,5,50,95,99,100]).tolist()))
    numerical_pass=bool(opt.success and max(kkt.values())<1e-6)
    receipt=dict(mode=mode,lambda_scaled=lam,sigma_assumed=PLAN['gaussian_optical_sigma_assumed'],unconstrained=cg_receipt,nonnegative=dict(success=bool(opt.success),message=str(opt.message),iterations=int(opt.nit),objective=float(opt.fun),max_projected_gradient=float(abs(pg).max()),kkt_by_block=kkt,numerical_PASS=numerical_pass),scales=dict(lunar=ms,solar=cs),source_nodes=dict(lunar=len(mi),solar=len(ci)),lunar_statistics=statistics,predictions=tests,seconds=time.time()-start)
    np.savez_compressed(OUT/f'B1_{mode}_scene.npz',lunar=lunar.reshape(shape),solar=solar.reshape(shape),lunar_indices=mi,solar_indices=ci,u=opt.x,scale=scale,**predictions)
    results.append(receipt);save('B1_native_scenes.json',dict(method=__doc__,results=results,train_stems=PLAN['train_stems'],reserved_stems=PLAN['reserved_stems'],scope='Native conditional effective weights and fixed core/geometry; numerical convergence is not physical validation. No image delivery.'))
    print(mode,'DONE',json.dumps(receipt['nonnegative']),'seconds',receipt['seconds'],flush=True)
    if not numerical_pass:raise RuntimeError('Constrained optimum not qualified; preserve checkpoint before interpreting results')
    del A,B,C,M,K,L,AM,AC;gc.collect()
