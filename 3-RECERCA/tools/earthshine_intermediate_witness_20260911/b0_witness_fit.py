"""Residualized scalar intermediate-scatter witness with frozen12px correction.
Training uses8frames;12earlier validation frames are retrospective, and8new
contact frames form two additional epoch tests. No new image source is made.
"""
from intermediate_common import *
rows=json.loads((OUT/'A0_inputs.json').read_text())['frames'];assert len(rows)==28;train=[r for r in rows if r['role']=='training'];test=[r for r in rows if r['role']!='training'];data={r['stem']:dict(np.load(OUT/f'A0_cells_{r["stem"]}.npz')) for r in rows};cells=np.unique(np.concatenate([data[r['stem']]['cell'] for r in train]));nc=len(cells);lookup=np.full((N//5)**2,-1);lookup[cells]=np.arange(nc);frame_lookup={r['stem']:i for i,r in enumerate([r for r in train if r['stem']!='572A2976'])};pc=3*len(frame_lookup)
def system(angular_half=None):
    idx=[];ys=[];ws=[];ps=[];ts=[];qs=[]
    for r in train:
        z=data[r['stem']];good=lookup[z['cell']]>=0
        if angular_half is not None:good &= (np.floor(z['angle']/(np.pi/6)).astype(int)%2)==angular_half
        n=int(good.sum());P=np.zeros((n,pc))
        if r['stem'] in frame_lookup:
            j=3*frame_lookup[r['stem']];P[:,j:j+3]=np.stack([np.ones(n),(z['cell_x'][good]-CX)/440,(z['cell_y'][good]-CY)/440],1)
        idx.append(lookup[z['cell'][good]]);ys.append(z['g'][good]);ws.append(1/(z['weight_variance'][good]*ALPHA));ps.append(P);ts.append(z['t'][good]);qs.append(z['q'][good])
    i=np.concatenate(idx);y=np.concatenate(ys);w=np.concatenate(ws);P=np.concatenate(ps);T=np.concatenate(ts);Q=np.concatenate(qs);D=np.bincount(i,weights=w,minlength=nc);safe=np.maximum(D,1e-30);B=np.stack([np.bincount(i,weights=w*P[:,j],minlength=nc) for j in range(pc)],1);H=P.T@(w[:,None]*P)-B.T@(B/safe[:,None]);assert np.linalg.matrix_rank(H)==pc
    def solve(v):
        b=np.bincount(i,weights=w*v,minlength=nc);rhs=P.T@(w*v)-B.T@(b/safe);planes=np.linalg.solve(H,rhs);m=(b-B@planes)/safe;return m,planes,m[i]+P@planes
    return dict(idx=i,y=y,w=w,P=P,T=T,Q=Q,D=D,solve=solve)
def fit(s,T,y=None):
    if y is None:y=s['y']
    tr=T-s['solve'](T)[2];yr=y-s['solve'](y)[2];H=np.sum(s['w']*tr*tr);rhs=np.sum(s['w']*tr*yr);assert H>0;uncon=rhs/H;f=float(np.clip(uncon,0,.1));return f,dict(unconstrained=float(uncon),nonnegative=f,at_bound=bool(f<1e-8 or f>.099999),residualized_power=float(H),conditional_se=float(1/np.sqrt(H)))
s=system();fa,ra=fit(s,s['T']);fn,rn=fit(s,s['Q']);models={}
for name,f,T in [('zero',0.,s['T']),('actual',fa,s['T']),('rotated',fn,s['Q'])]:
    m,planes,pred=s['solve'](s['y']-f*T);models[name]=dict(f=f,m=m,planes=planes);np.savez_compressed(OUT/f'B0_{name}_model.npz',cells=cells,lunar_nuisance=m,frame_planes=planes,witness_coefficient=f);print(name,'coefficient',f,'training weightedMSE',float(np.mean(s['w']*(pred+f*T-s['y'])**2)),flush=True)
cell_x=(cells%(N//5)+.5)*5;cell_y=(cells//(N//5)+.5)*5;truth=650+40*np.sin(cell_x/17)*np.cos(cell_y/23);ysyn=truth[s['idx']]+s['P']@(np.sin(np.arange(pc))*30)+s['T']*.02;fi,_=fit(s,s['T'],ysyn);assert abs(fi-.02)<1e-8
halves=[]
for half in [0,1]:
    ss=system(half);_,rr=fit(ss,ss['T']);halves.append(dict(half=half,**rr))
epoch_parts={};frame_results=[]
for r in test:
    stem=r['stem'];z=data[stem];ii=lookup[z['cell']];good=ii>=0;good[good]&=s['D'][ii[good]]>0;i=ii[good];rad=z['radius'][good];ang=z['angle'][good];obs=z['g'][good];P=np.stack([np.ones(len(i)),(z['cell_x'][good]-CX)/440,(z['cell_y'][good]-CY)/440],1);w=1/(z['weight_variance'][good]*ALPHA+1/np.maximum(s['D'][i],1e-30));cal=(rad>=415)&(rad<423);assert cal.sum()>=50;predictions={};planes={}
    for name,model in models.items():
        T=z['q'][good] if name=='rotated' else z['t'][good];pred=model['m'][i]+model['f']*T;pp=np.linalg.lstsq(P[cal]*np.sqrt(w[cal,None]),(obs[cal]-pred[cal])*np.sqrt(w[cal]),rcond=None)[0];predictions[name]=pred+P@pp;planes[name]=pp.tolist()
    regions=[]
    for lo,hi in [(426,435),(435,445),(445,449),(426,449)]:
        use=(rad>=lo)&(rad<hi);regions.append(dict(radius=[lo,hi],cells=int(use.sum()),weighted_MSE={k:float(np.mean(w[use]*(v[use]-obs[use])**2)) if use.any() else None for k,v in predictions.items()},median_residual_G={k:float(np.median(v[use]-obs[use])) if use.any() else None for k,v in predictions.items()}))
    score=(rad>=426)&(rad<449)
    for sector in range(12):
        use=score&(np.floor(ang/(np.pi/6)).astype(int)==sector)
        if use.any():epoch_parts.setdefault(r['epoch'],[]).append(dict(stem=stem,role=r['role'],sector=sector,n=int(use.sum()),SSE={k:float(np.sum(w[use]*(v[use]-obs[use])**2)) for k,v in predictions.items()}))
    np.savez_compressed(OUT/f'B0_validation_{stem}.npz',radius=rad,angle=ang,g=obs,weight=w,cell=z['cell'][good],**predictions);frame_results.append(dict(stem=stem,role=r['role'],epoch=r['epoch'],planes=planes,regions=regions))
epochs=[];sectors=[]
for epoch,rr in epoch_parts.items():
    n=sum(r['n'] for r in rr);mse={k:sum(r['SSE'][k] for r in rr)/n for k in models};epochs.append(dict(epoch=epoch,role=rr[0]['role'],cells=n,weighted_MSE=mse,reduction_percent=100*(1-mse['actual']/mse['zero']),rotated_reduction_percent=100*(1-mse['rotated']/mse['zero'])))
    for sector in range(12):
        rs=[r for r in rr if r['sector']==sector];n=sum(r['n'] for r in rs)
        if n>=50:
            ratio=sum(r['SSE']['actual'] for r in rs)/sum(r['SSE']['zero'] for r in rs);sectors.append(dict(epoch=epoch,role=rr[0]['role'],sector=sector,cells=n,ratio=ratio,no_worse=bool(ratio<=1.02)))
fraction=float(np.mean([r['no_worse'] for r in sectors]));passed=bool(len(epochs)==6 and all(r['reduction_percent']>=5 for r in epochs) and fraction>=.75 and sum(r['weighted_MSE']['actual']<r['weighted_MSE']['rotated'] for r in epochs)>=5 and not ra['at_bound'])
save('B0_intermediate_witness.json',dict(method=__doc__,p12_frozen=P12,intermediate_sigma=4,actual=ra,rotated=rn,angular_halves=halves,exact_linear_injection=dict(input=.02,recovered=fi,PASS=abs(fi-.02)<1e-8),epochs=epochs,sectors=sectors,no_worse_sector_fraction=fraction,witness_PASS=passed,frame_results=frame_results,limits=json.loads((OUT/'PLAN.json').read_text())['limitations'],source_or_PSB_changed=False));print(json.dumps(dict(actual=ra,rotated=rn,angular_halves=halves,epochs=epochs,sector_fraction=fraction,PASS=passed)),flush=True)
