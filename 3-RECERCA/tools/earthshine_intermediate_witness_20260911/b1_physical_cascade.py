"""Fit the positive4px mixture after frozen12px correction, retaining the core.
Exact five-term mixture inverse on common observed support. Coefficients are
conditional on this two-scale cascade, not a unique instrument PSF.
"""
from intermediate_common import *
from scipy.optimize import minimize_scalar
import ast
rows=json.loads((OUT/'A1_inputs.json').read_text())['frames'];assert len(rows)==28;train=[r for r in rows if r['role']=='training'];test=[r for r in rows if r['role']!='training'];data={r['stem']:dict(np.load(OUT/f'A1_cells_{r["stem"]}.npz')) for r in rows};cells=np.unique(np.concatenate([data[r['stem']]['cell'] for r in train]));nc=len(cells);lookup=np.full((N//5)**2,-1);lookup[cells]=np.arange(nc);frame_lookup={r['stem']:i for i,r in enumerate([r for r in train if r['stem']!='572A2976'])};pc=3*len(frame_lookup)
fn=next(r for r in ast.parse((HERE/'b0_witness_fit.py').read_text()).body if isinstance(r,ast.FunctionDef) and r.name=='system');exec(compile(ast.Module(body=[fn],type_ignores=[]),'frozen_nuisance_system','exec'))
def coefficients(p):
    a=p/(1-p);return np.array([(-1)**(k+1)*a**k for k in range(1,6)])
def terms(half=None,null=False):
    ans=[]
    for r in train:
        z=data[r['stem']];good=lookup[z['cell']]>=0
        if half is not None:good &= (np.floor(z['angle']/(np.pi/6)).astype(int)%2)==half
        ans.append(np.stack([z[('q' if null else 't')+str(k)][good] for k in range(1,6)],1))
    return np.concatenate(ans)
def fit(s,T,y=None):
    if y is None:y=s['y']
    yr=y-s['solve'](y)[2];tr=T-np.stack([s['solve'](T[:,j])[2] for j in range(5)],1);H=tr.T@(s['w'][:,None]*tr);rhs=tr.T@(s['w']*yr)
    def obj(p):
        c=coefficients(p);return .5*c@H@c-rhs@c
    opt=minimize_scalar(obj,bounds=(0,.1),method='bounded',options={'xatol':1e-13});assert opt.success;grid=np.array([obj(p) for p in np.linspace(0,.1,101)]);assert opt.fun<=grid.min()+1e-8;return float(opt.x),dict(p=float(opt.x),at_bound=bool(opt.x<1e-6 or opt.x>.09999),objective_gain=float(-opt.fun),grid_minimum=float(grid.min()))
s=system();T=terms();Q=terms(null=True);pa,ra=fit(s,T);pn,rn=fit(s,Q);models={}
for name,p,t in [('zero',0.,T),('actual',pa,T),('rotated',pn,Q)]:
    c=coefficients(p);m,planes,pred=s['solve'](s['y']-t@c);models[name]=dict(p=p,c=c,m=m,planes=planes);np.savez_compressed(OUT/f'B1_{name}_model.npz',cells=cells,lunar_nuisance=m,frame_planes=planes,p4=p,p12=P12,inverse_coefficients=c);print(name,p,'training weightedMSE',float(np.mean(s['w']*(pred+t@c-s['y'])**2)),flush=True)
halves=[]
for half in [0,1]:
    ss=system(half);_,rr=fit(ss,terms(half));halves.append(dict(half=half,**rr))
cell_x=(cells%(N//5)+.5)*5;cell_y=(cells//(N//5)+.5)*5;truth=650+40*np.sin(cell_x/17)*np.cos(cell_y/23);ysyn=truth[s['idx']]+s['P']@(np.sin(np.arange(pc))*30)+T@coefficients(.02);fi,_=fit(s,T,ysyn);assert abs(fi-.02)<1e-8
aw=P12/(1-P12);ai=pa/(1-pa);rawmax=max(r['maximum_abs_observed_G'] for r in rows);wide_bound=aw**5/(1-P12)/(1-aw)*rawmax;z_bound=rawmax/(1-2*P12);intermediate_bound=ai**6/(1-pa)/(1-ai)*z_bound;remainder=wide_bound/(1-2*pa)+intermediate_bound
parts={};frame_results=[]
for r in test:
    stem=r['stem'];z=data[stem];ii=lookup[z['cell']];good=ii>=0;good[good]&=s['D'][ii[good]]>0;i=ii[good];rad=z['radius'][good];ang=z['angle'][good];obs=z['g'][good];P=np.stack([np.ones(len(i)),(z['cell_x'][good]-CX)/440,(z['cell_y'][good]-CY)/440],1);w=1/(z['weight_variance'][good]*ALPHA+1/np.maximum(s['D'][i],1e-30));cal=(rad>=415)&(rad<423);assert cal.sum()>=50;predictions={};planes={}
    for name,model in models.items():
        TT=np.stack([z[('q' if name=='rotated' else 't')+str(k)][good] for k in range(1,6)],1);pred=model['m'][i]+TT@model['c'];pp=np.linalg.lstsq(P[cal]*np.sqrt(w[cal,None]),(obs[cal]-pred[cal])*np.sqrt(w[cal]),rcond=None)[0];predictions[name]=pred+P@pp;planes[name]=pp.tolist()
    regions=[]
    for lo,hi in [(426,435),(435,445),(445,449),(426,449)]:
        use=(rad>=lo)&(rad<hi);regions.append(dict(radius=[lo,hi],cells=int(use.sum()),weighted_MSE={k:float(np.mean(w[use]*(v[use]-obs[use])**2)) if use.any() else None for k,v in predictions.items()},median_residual_G={k:float(np.median(v[use]-obs[use])) if use.any() else None for k,v in predictions.items()}))
    score=(rad>=426)&(rad<449)
    for sector in range(12):
        use=score&(np.floor(ang/(np.pi/6)).astype(int)==sector)
        if use.any():parts.setdefault(r['epoch'],[]).append(dict(stem=stem,role=r['role'],sector=sector,n=int(use.sum()),SSE={k:float(np.sum(w[use]*(v[use]-obs[use])**2)) for k,v in predictions.items()}))
    np.savez_compressed(OUT/f'B1_validation_{stem}.npz',radius=rad,angle=ang,g=obs,weight=w,cell=z['cell'][good],**predictions);frame_results.append(dict(stem=stem,role=r['role'],epoch=r['epoch'],planes=planes,regions=regions))
epochs=[];sectors=[]
for epoch,rr in parts.items():
    n=sum(r['n'] for r in rr);mse={k:sum(r['SSE'][k] for r in rr)/n for k in models};epochs.append(dict(epoch=epoch,role=rr[0]['role'],cells=n,weighted_MSE=mse,reduction_percent=100*(1-mse['actual']/mse['zero']),rotated_reduction_percent=100*(1-mse['rotated']/mse['zero'])))
    for sector in range(12):
        rs=[r for r in rr if r['sector']==sector];n=sum(r['n'] for r in rs)
        if n>=50:
            ratio=sum(r['SSE']['actual'] for r in rs)/sum(r['SSE']['zero'] for r in rs);sectors.append(dict(epoch=epoch,role=rr[0]['role'],sector=sector,cells=n,ratio=ratio,no_worse=bool(ratio<=1.02)))
fraction=float(np.mean([r['no_worse'] for r in sectors]));passed=bool(len(epochs)==6 and all(r['reduction_percent']>=5 for r in epochs) and fraction>=.75 and sum(r['weighted_MSE']['actual']<r['weighted_MSE']['rotated'] for r in epochs)>=5 and not ra['at_bound'] and remainder<=.1)
save('B1_physical_cascade.json',dict(method=__doc__,p12_frozen=P12,p4=pa,actual=ra,rotated=rn,angular_halves=halves,inverse_coefficients=coefficients(pa).tolist(),neumann_bound_G=remainder,wide_remainder_bound_G=wide_bound,intermediate_remainder_bound_G=intermediate_bound,exact_design_injection=dict(input=.02,recovered=fi,PASS=abs(fi-.02)<1e-8),epochs=epochs,sectors=sectors,no_worse_sector_fraction=fraction,temporal_cascade_PASS=passed,frame_results=frame_results,limits=json.loads((OUT/'PLAN.json').read_text())['limitations'],source_or_PSB_changed=False));print(json.dumps(dict(p4=pa,halves=halves,remainder=remainder,epochs=epochs,sector_fraction=fraction,PASS=passed)),flush=True)
