"""Fit the core-preserving mixture inverse, retaining the original train split.
The broad optical component is G12 convolved with the unknown narrow core.
"""
from scatter_common import *
from scipy.optimize import minimize_scalar
import ast
plan=json.loads((OUT/'PLAN.json').read_text());rows=json.loads((OUT/'A0_witness_inputs.json').read_text())['frames'];train=[r for r in rows if r['train']];test=[r for r in rows if not r['train']];data={r['stem']:dict(np.load(OUT/f'A0_cells_{r["stem"]}.npz')) for r in rows};ALPHA=14.826313721285086;cells=np.unique(np.concatenate([data[r['stem']]['cell'] for r in train]));nc=len(cells);lookup=np.full((N//5)**2,-1);lookup[cells]=np.arange(nc);frame_lookup={r['stem']:i for i,r in enumerate(train) if r['stem']!='572A2976'};frame_lookup={k:i for i,k in enumerate(frame_lookup)};pcount=3*len(frame_lookup)
tree=ast.parse((HERE/'b0_witness_fit.py').read_text());fn=next(a for a in tree.body if isinstance(a,ast.FunctionDef) and a.name=='system');exec(compile(ast.Module(body=[fn],type_ignores=[]),str(HERE/'b0_witness_fit.py'),'exec'))
terms={r['stem']:dict(np.load(OUT/f'A1_terms_{r["stem"]}.npz')) for r in rows}
def term_matrix(half=None):
    values=[]
    for r in train:
        stem=r['stem'];z=data[stem];good=lookup[z['cell']]>=0
        if half is not None:good &= (np.floor(z['angle']/(np.pi/6)).astype(int)%2)==half
        values.append(np.stack([terms[stem][f'b{k}'][good] for k in range(1,5)],1))
    return np.concatenate(values)
def coefficients(p):
    a=p/(1-p);return np.array([a,-a*a,a**3,-a**4])
def fit(half=None):
    s=system(train,half);T=term_matrix(half);yr=s['y']-s['solve'](s['y'])[2];tr=T-s['solve'](T)[2];H=tr.T@(s['w'][:,None]*tr);rhs=tr.T@(s['w']*yr)
    def objective(p):
        v=coefficients(p);return .5*v@H@v-rhs@v
    opt=minimize_scalar(objective,bounds=(0,.10),method='bounded',options={'xatol':1e-12});assert opt.success;return float(opt.x),s,T,dict(half=half,p=float(opt.x),objective_gain=float(-opt.fun),at_bound=bool(opt.x<1e-6 or opt.x>.09999))
p,s,T,main=fit();halves=[fit(h)[3] for h in [0,1]];c=coefficients(p);m,planes,pred=s['solve'](s['y']-T@c);zero=s['solve'](s['y']);old=np.load(OUT/'B0_zero_model.npz');assert np.max(abs(zero[0]-old['lunar_nuisance']))<1e-10
native_bounds=json.loads((OUT/'A1_neumann_terms.json').read_text())['frames'];aa=p/(1-p);bounds=[dict(stem=r['stem'],remainder_max_G=aa**5/(1-p)/(1-aa)*r['maximum_abs_observed_valid_G']) for r in native_bounds];remainder=max(r['remainder_max_G'] for r in bounds);assert remainder<.1,remainder
np.savez_compressed(OUT/'B1_physical_model.npz',p=p,cells=cells,lunar_nuisance=m,lunar_core_estimate=m/(1-p),frame_planes=planes,inverse_coefficients=c)
summaries={};predictions=[]
for r in test:
    stem=r['stem'];z=data[stem];ii=lookup[z['cell']];valid=ii>=0;valid[valid] &= s['D'][ii[valid]]>0;i=ii[valid];rad=z['radius'][valid];ang=z['angle'][valid];obs=z['g'][valid];A=np.stack([np.ones(len(i)),(z['cell_x'][valid]-CX)/440,(z['cell_y'][valid]-CY)/440],1);weight=1/(z['weight_variance'][valid]*ALPHA+1/np.maximum(s['D'][i],1e-30));cal=(rad>=415)&(rad<423);terms_frame=np.stack([terms[stem][f'b{k}'][valid] for k in range(1,5)],1);expected={}
    for mode,base,coeff in [('zero',zero[0],np.zeros(4)),('physical',m,c)]:
        pp=base[i]+terms_frame@coeff;offset=np.linalg.lstsq(A[cal]*np.sqrt(weight[cal,None]),(obs[cal]-pp[cal])*np.sqrt(weight[cal]),rcond=None)[0];expected[mode]=pp+A@offset
    for sector in range(12):
        keep=(rad>=426)&(rad<445)&(np.floor(ang/(np.pi/6)).astype(int)==sector)
        if keep.sum():summaries.setdefault(r['epoch'],[]).append(dict(sector=sector,n=int(keep.sum()),SSE={k:float(np.sum(weight[keep]*(pred[keep]-obs[keep])**2)) for k,pred in expected.items()}))
    np.savez_compressed(OUT/f'B1_validation_{stem}.npz',radius=rad,angle=ang,g=obs,weight=weight,**expected);predictions.append(dict(stem=stem,epoch=r['epoch']))
epochs=[];sectors=[]
for epoch,rr in summaries.items():
    n=sum(r['n'] for r in rr);mse={k:sum(r['SSE'][k] for r in rr)/n for k in ['zero','physical']};epochs.append(dict(epoch=epoch,cells=n,weighted_MSE=mse,reduction_percent=100*(1-mse['physical']/mse['zero'])))
    for sector in range(12):
        rs=[r for r in rr if r['sector']==sector];n=sum(r['n'] for r in rs)
        if n>=50:
            a=sum(r['SSE']['physical'] for r in rs);b=sum(r['SSE']['zero'] for r in rs);sectors.append(dict(epoch=epoch,sector=sector,cells=n,ratio=a/b,no_worse=a<=1.02*b))
fraction=float(np.mean([r['no_worse'] for r in sectors]));passed=all(r['reduction_percent']>=5 for r in epochs) and fraction>=.75 and not main['at_bound']
receipt=dict(method=__doc__,p=p,broad_incremental_sigma=12,fit=main,angular_halves=halves,narrow_core='Unknown and retained; not deconvolved',inverse_coefficients=c.tolist(),neumann_remainder_max_G=remainder,neumann_bounds=bounds,new_epoch_summary=epochs,sectors=sectors,no_worse_sector_fraction=fraction,temporal_mixture_PASS=bool(passed),native_sampling_and_injection_PASS=False,source_or_PSB_changed=False,limits=['Physical-mixture candidate conditional on inherited registration/calibration and incomplete-pixel normalization','Temporal prediction alone does not prove recovered lunar textures; native sampling and injection still required','No correction of saturated native pixels or core PSF is claimed']);save('B1_physical_mixture.json',receipt);print(json.dumps(receipt),flush=True)
