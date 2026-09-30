"""Residualize lunar-cell radiance and frame planes before estimating scatter.
Only the two training epochs select shared coefficients. Four other epochs
test predictions, with each new frame's plane calibrated only at415-423px.
"""
from scatter_common import *
from scipy.optimize import minimize
plan=json.loads((OUT/'PLAN.json').read_text());rows=json.loads((OUT/'A0_witness_inputs.json').read_text())['frames'];assert len(rows)==20;train=[r for r in rows if r['train']];test=[r for r in rows if not r['train']];data={r['stem']:dict(np.load(OUT/f'A0_cells_{r["stem"]}.npz')) for r in rows};ALPHA=14.826313721285086
save('B0_fit_plan.json',dict(method=__doc__,reference_frame='572A2976',native_cells='same physical5px cell, common latent lunar mean and plane nuisance per frame',coefficient_bounds='f>=0;sum(f)<=0.10',validation_nuisance='Plane fitted in415-423px only; all scores426-445px reserved',witness_gate='At least5percent weightedMSE reduction versus refitted zero-scatter model in EACH of four withheld epochs, and no more than2percent worsening in at least75percent of qualified epoch/sector bins. At least3epochs must prefer actual-angle over rotated control.',linear_control='Known0.02,0.01 coefficient injection through same design, error<1e-8; estimator check only, not PSF recovery',limits=plan['limitations']))
cells=np.unique(np.concatenate([data[r['stem']]['cell'] for r in train]));nc=len(cells);lookup=np.full((N//5)**2,-1);lookup[cells]=np.arange(nc);frame_lookup={r['stem']:i for i,r in enumerate(train) if r['stem']!='572A2976'};frame_lookup={k:i for i,k in enumerate(frame_lookup)};pcount=3*len(frame_lookup)
def system(rows_used,angular_half=None):
    idx=[];values=[];weights=[];cov=[];true=[];null=[];frames=[]
    for r in rows_used:
        s=r['stem'];z=data[s];good=(lookup[z['cell']]>=0)
        if angular_half is not None:good &= (np.floor(z['angle']/(np.pi/6)).astype(int)%2)==angular_half
        n=int(good.sum());i=lookup[z['cell'][good]];P=np.zeros((n,pcount))
        if s in frame_lookup:
            j=3*frame_lookup[s];P[:,j:j+3]=np.stack([np.ones(n),(z['cell_x'][good]-CX)/440,(z['cell_y'][good]-CY)/440],1)
        idx.append(i);values.append(z['g'][good]);weights.append(1/(z['weight_variance'][good]*ALPHA));cov.append(P);true.append(np.stack([z['t0'][good],z['t2'][good]],1));null.append(np.stack([z['t1'][good],z['t3'][good]],1));frames.extend([s]*n)
    idx=np.concatenate(idx);y=np.concatenate(values);w=np.concatenate(weights);P=np.concatenate(cov);T=np.concatenate(true);Q=np.concatenate(null);D=np.bincount(idx,weights=w,minlength=nc);B=np.stack([np.bincount(idx,weights=w*P[:,j],minlength=nc) for j in range(pcount)],1);Dsafe=np.maximum(D,1e-30);H=P.T@(w[:,None]*P)-B.T@(B/Dsafe[:,None]);rank=np.linalg.matrix_rank(H);assert rank==pcount,(rank,pcount)
    def solve(v):
        vector=v.ndim==1;V=v[:,None] if vector else v;b=np.stack([np.bincount(idx,weights=w*V[:,j],minlength=nc) for j in range(V.shape[1])],1);rhs=P.T@(w[:,None]*V)-B.T@(b/Dsafe[:,None]);planes=np.linalg.solve(H,rhs);m=(b-B@planes)/Dsafe[:,None];pred=m[idx]+P@planes;return (m[:,0],planes[:,0],pred[:,0]) if vector else (m,planes,pred)
    return dict(idx=idx,y=y,w=w,P=P,T=T,Q=Q,D=D,solve=solve,frames=frames)
s=system(train);y=s['y'];w=s['w'];base=s['solve'](y);yr=y-base[2]
def fit_coeff(T,system=s):
    tr=T-system['solve'](T)[2];yr=system['y']-system['solve'](system['y'])[2];H=tr.T@(system['w'][:,None]*tr);rhs=tr.T@(system['w']*yr);uncon=np.linalg.solve(H,rhs)
    scale=max(np.max(abs(rhs)),1)
    opt=minimize(lambda f:(.5*f@H@f-rhs@f)/scale,np.clip(uncon,0,.049),jac=lambda f:(H@f-rhs)/scale,bounds=[(0,.1)]*2,constraints=[dict(type='ineq',fun=lambda f:.1-f.sum(),jac=lambda f:-np.ones(2))],method='SLSQP',options={'ftol':1e-13,'maxiter':500});assert opt.success,opt.message
    return opt.x,dict(unconstrained=uncon.tolist(),nonnegative=opt.x.tolist(),sum=float(opt.x.sum()),hessian_condition=float(np.linalg.cond(H)),residualized_template_correlation=float(H[0,1]/np.sqrt(H[0,0]*H[1,1])),optimizer=str(opt.message))
f,fr=fit_coeff(s['T']);fn,fnr=fit_coeff(s['Q']);models={}
for name,coeff,T in [('zero',np.zeros(2),s['T']),('actual',f,s['T']),('rotated',fn,s['Q'])]:
    m,planes,pred=s['solve'](y-T@coeff);pred+=T@coeff;models[name]=dict(coeff=coeff,m=m,planes=planes);np.savez_compressed(OUT/f'B0_{name}_model.npz',cells=cells,lunar_nuisance=m,frame_planes=planes,coefficients=coeff,predictions=pred);print(name,'coeff',coeff,'weightedMSE',float(np.mean(w*(pred-y)**2)),flush=True)
# Exact design-injection check, including a nonflat lunar field.
cell_x=(cells%(N//5)+.5)*5;cell_y=(cells//5+.5)*5;truth=650+40*np.sin(cell_x/17)*np.cos(cell_y/23);plane_truth=np.sin(np.arange(pcount))*30;injected=np.array([.02,.01]);ysyn=truth[s['idx']]+s['P']@plane_truth+s['T']@injected;ss=dict(s,y=ysyn);fi,fir=fit_coeff(s['T'],ss);injection_error=float(np.max(abs(fi-injected)));assert injection_error<1e-8,injection_error
halves=[]
for half in [0,1]:
    ss=system(train,half);ff,rec=fit_coeff(ss['T'],ss);halves.append(dict(half=half,**rec))
results=[];epoch_values={}
for r in test:
    stem=r['stem'];z=data[stem];i=lookup[z['cell']];valid=(i>=0);valid[valid] &= s['D'][i[valid]]>0;i=i[valid];rad=z['radius'][valid];ang=z['angle'][valid];obs=z['g'][valid];P=np.stack([np.ones(len(i)),(z['cell_x'][valid]-CX)/440,(z['cell_y'][valid]-CY)/440],1);weight=1/(z['weight_variance'][valid]*ALPHA+1/np.maximum(s['D'][i],1e-30));cal=(rad>=415)&(rad<423);score=(rad>=426)&(rad<445);assert cal.sum()>=50
    predictions={};planes={}
    for name,model in models.items():
        T=np.stack([z['t1'][valid],z['t3'][valid]],1) if name=='rotated' else np.stack([z['t0'][valid],z['t2'][valid]],1);pred=model['m'][i]+T@model['coeff'];pp=np.linalg.lstsq(P[cal]*np.sqrt(weight[cal,None]),(obs[cal]-pred[cal])*np.sqrt(weight[cal]),rcond=None)[0];pred+=P@pp;predictions[name]=pred;planes[name]=pp.tolist()
    region_rows=[]
    for lo,hi in [(426,435),(435,445),(426,445)]:
        keep=(rad>=lo)&(rad<hi);region_rows.append(dict(radius=[lo,hi],cells=int(keep.sum()),weighted_MSE={k:float(np.mean(weight[keep]*(v[keep]-obs[keep])**2)) for k,v in predictions.items()},median_residual_G={k:float(np.median(v[keep]-obs[keep])) for k,v in predictions.items()}))
    er=epoch_values.setdefault(r['epoch'],[])
    for sector in range(12):
        keep=score&(np.floor(ang/(np.pi/6)).astype(int)==sector)
        if keep.sum():er.append(dict(stem=stem,sector=sector,n=int(keep.sum()),weighted_SSE={k:float(np.sum(weight[keep]*(v[keep]-obs[keep])**2)) for k,v in predictions.items()}))
    results.append(dict(stem=stem,epoch=r['epoch'],planes_from_control=planes,regions=region_rows));np.savez_compressed(OUT/f'B0_validation_{stem}.npz',radius=rad,angle=ang,cell=z['cell'][valid],g=obs,weight=weight,**predictions)
summary=[];sector_scores=[]
for epoch,rr in epoch_values.items():
    n=sum(r['n'] for r in rr);mse={k:sum(r['weighted_SSE'][k] for r in rr)/n for k in models};summary.append(dict(epoch=epoch,cells=n,weighted_MSE=mse,actual_reduction_percent=100*(1-mse['actual']/mse['zero']),rotated_reduction_percent=100*(1-mse['rotated']/mse['zero'])))
    for sector in range(12):
        rs=[r for r in rr if r['sector']==sector];n=sum(r['n'] for r in rs)
        if n<50:continue
        mse={k:sum(r['weighted_SSE'][k] for r in rs)/n for k in models};sector_scores.append(dict(epoch=epoch,sector=sector,cells=n,weighted_MSE=mse,no_worse=bool(mse['actual']<=1.02*mse['zero'])))
fraction=float(np.mean([r['no_worse'] for r in sector_scores]));passed=all(r['actual_reduction_percent']>=5 for r in summary) and fraction>=.75 and sum(r['weighted_MSE']['actual']<r['weighted_MSE']['rotated'] for r in summary)>=3
receipt=dict(method=__doc__,actual_coefficients=fr,rotated_coefficients=fnr,angular_halves=halves,linear_injection=dict(input=injected.tolist(),recovered=fi.tolist(),max_error=injection_error,PASS=injection_error<1e-8),new_epoch_summary=summary,sector_scores=sector_scores,no_worse_sector_fraction=fraction,temporal_witness_PASS=bool(passed),frame_predictions=results,limits=plan['limitations']);save('B0_temporal_witness_fit.json',receipt);print(json.dumps(dict(coefficients=fr,halves=halves,summary=summary,sector_fraction=fraction,PASS=passed)),flush=True)
