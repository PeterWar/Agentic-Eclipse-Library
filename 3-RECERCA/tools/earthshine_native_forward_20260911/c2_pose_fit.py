"""Compare refitted native scenes using fixed, spatially withheld pose/core.
Six short exposures train; two distinct short exposures reserve all target pixels.
"""
from fit_system import *
from scipy.sparse.linalg import LinearOperator,cg
from scipy.optimize import minimize
import time,gc
plan=json.loads((OUT/'C1_pose_operator_plan.json').read_text());rows=json.loads((OUT/'C1_pose_operators.json').read_text())['frames'];assert len(rows)==8
folder=OUT/'pose_matrices';geo=Geometry(16);train=[r for r in rows if r['train']];data={r['stem']:dict(np.load(OUT/'matrices'/f'{r["stem"]}_observations.npz')) for r in rows};lam=plan['lambda_scaled'];alpha=14.826313721285086
inside=[];outside=[]
for r in train:
    z=data[r['stem']];rr=np.hypot(z['xy'][:,0]-CX,z['xy'][:,1]-CY);inside.extend(z['g'][rr<435]);outside.extend(z['g'][rr>465])
ms=float(np.median(inside));cs=float(np.median(outside));results=[]
for variant in plan['variants']:
    start=time.time();AM=[];AC=[];weights=[];target=[]
    for r in train:
        s=r['stem'];z=data[s];AM.append(load_npz(folder/f'{s}_{variant}_lunar.npz'));AC.append(load_npz(folder/f'{s}_{variant}_solar.npz'));weights.append(z['q']/(z['weight_variance']*alpha));target.append(z['g'])
    M=vstack(AM,format='csr');C=vstack(AC,format='csr');w=np.concatenate(weights);mi=np.flatnonzero(np.asarray(M.power(2).T@w).ravel()>1e-20);ci=np.flatnonzero(np.asarray(C.power(2).T@w).ravel()>1e-20)
    A=hstack([M[:,mi]*ms,C[:,ci]*cs],format='csr').multiply(np.sqrt(w)[:,None]).tocsr();b=np.concatenate(target)*np.sqrt(w);L=block_diag([laplacian(mi,geo),laplacian(ci,geo)],format='csr');eps=1e-10;diag=np.asarray(A.power(2).sum(0)).ravel()+lam*np.asarray(L.power(2).sum(0)).ravel()+eps;scale=1/np.sqrt(diag);B=A.multiply(scale[None,:]).tocsr();K=L.multiply(scale[None,:]).tocsr();rhs=B.T@b
    def normal(u):return B.T@(B@u)+lam*(K.T@(K@u))+eps*scale**2*u
    def objective(u):
        rr=B@u-b;kk=K@u;return .5*np.dot(rr,rr)+.5*lam*np.dot(kk,kk)+.5*eps*np.dot(scale*u,scale*u),B.T@rr+lam*(K.T@kk)+eps*scale**2*u
    count=[0]
    def callback(u):
        count[0]+=1
        if count[0]%300==0:print(variant,'CG',count[0],flush=True)
    u,info=cg(LinearOperator((len(rhs),len(rhs)),matvec=normal,dtype=np.float64),rhs,x0=np.ones(len(rhs))/scale,rtol=1e-9,maxiter=4000,callback=callback);res=normal(u)-rhs;cgblocks={k:float(np.linalg.norm(res[a])/max(np.linalg.norm(rhs[a]),1e-30)) for k,a in [('lunar',slice(None,len(mi))),('solar',slice(len(mi),None))]}
    assert info==0 and max(cgblocks.values())<1e-6,(info,cgblocks)
    negative=int(np.sum((u*scale)[:len(mi)]<0));minimum=float(np.min((u*scale)[:len(mi)]*ms));print(variant,'CG DONE',count[0],'negative',negative,'minimum',minimum,flush=True)
    iterations=[0]
    def cb(v):
        iterations[0]+=1
        if iterations[0]%250==0:
            f,g=objective(v);print(variant,'L-BFGS',iterations[0],f,flush=True);np.savez_compressed(OUT/f'C2_{variant}_checkpoint.npz',u=v,scale=scale,mi=mi,ci=ci,ms=ms,cs=cs)
    opt=minimize(objective,np.maximum(u,0),method='L-BFGS-B',jac=True,bounds=[(0,None)]*len(u),callback=cb,options={'maxiter':2500,'maxcor':25,'ftol':0,'gtol':1e-7,'maxls':50});f,g=objective(opt.x);pg=np.where((opt.x<=1e-10)&(g>0),0,g);kkt={k:float(np.max(abs(pg[a]))/max(np.max(abs(rhs[a])),1)) for k,a in [('lunar',slice(None,len(mi))),('solar',slice(len(mi),None))]};passed=max(kkt.values())<1e-6
    v=opt.x*scale;lunar=np.zeros(geo.size);solar=lunar.copy();lunar[mi]=v[:len(mi)]*ms;solar[ci]=v[len(mi):]*cs;preds={};tests=[]
    for r in rows:
        s=r['stem'];z=data[s];p=load_npz(folder/f'{s}_{variant}_lunar.npz')@lunar+load_npz(folder/f'{s}_{variant}_solar.npz')@solar;preds[s]=p;w=z['q']/(z['weight_variance']*alpha);rr=np.hypot(z['xy'][:,0]-CX,z['xy'][:,1]-CY);regions=[]
        for lo,hi in [(415,435),(435,445),(445,449),(449,454),(454,480),(480,500)]:
            use=(rr>=lo)&(rr<hi)
            if use.sum()<20:continue
            d=p[use]-z['g'][use];regions.append(dict(radius=[lo,hi],samples=int(use.sum()),weighted_mean_square=float(np.mean(w[use]*d*d)),median_residual_G=float(np.median(d)),rms_residual_G=float(np.sqrt(np.mean(d*d)))))
        tests.append(dict(stem=s,reserved=not r['train'],regions=regions))
    yy,xx=np.mgrid[geo.box[1]:geo.box[3]+1,geo.box[0]:geo.box[2]+1];rr=np.hypot(xx-CX,yy-CY);use=(xx<geo.border(yy))&(xx>=1117)&(xx<=1187)&(yy>=630)&(yy<=770);lm=lunar.reshape(geo.shape);stats=[]
    for lo,hi in [(415,435),(435,445),(445,449),(449,454)]:
        mask=use&(rr>=lo)&(rr<hi)
        if mask.sum():stats.append(dict(radius=[lo,hi],quantiles=np.percentile(lm[mask],[0,5,50,95,100]).tolist()))
    receipt=dict(variant=variant,numerical_PASS=passed,unconstrained_negative_nodes=negative,unconstrained_minimum_G=minimum,constrained_iterations=int(opt.nit),optimizer_message=str(opt.message),kkt_by_block=kkt,objective=float(f),scales=[ms,cs],lambda_scaled=lam,lunar_statistics=stats,predictions=tests,seconds=time.time()-start)
    np.savez_compressed(OUT/f'C2_{variant}_scene.npz',lunar=lm,solar=solar.reshape(geo.shape),u=opt.x,scale=scale,lunar_indices=mi,solar_indices=ci,**preds);results.append(receipt);save('C2_pose_fits.json',dict(method=__doc__,results=results,limits=plan['limits']));print(variant,'DONE',json.dumps({k:receipt[k] for k in ['numerical_PASS','objective','kkt_by_block','seconds']}),flush=True)
    del AM,AC,M,C,A,B,K,L;gc.collect()
