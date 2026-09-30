"""Fixed-kernel heldout temporal check, with identical nuisance freedoms.
Kernel training cells exclude the last six pixels. Common lunar templates use
training captures only; each reserved frame's plane uses r260..350 only.
The opposite-green predictors contain disjoint photons, shared calibration.
"""
from common50 import *
from scipy.linalg import cho_factor,cho_solve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fit=json.loads((OUT/'A1_fit.json').read_text());p=np.array(fit['p']);meta={r['stem']:r for r in json.loads((NATIVE/'D1_inputs.json').read_text())['frames']}
frames=json.loads((ROOT/'output/earthshine_diffraction_20260912/A2_stack_plan.json').read_text())['frames'];data={}
for r in frames:
    stem=r['stem'];z=dict(np.load(OUT/f'A1_observations_{stem}.npz'));c=np.load(OUT/f'A1_corrected_cells_{stem}.npz');z['scatter']=c['scatter'];z['corrected']=c['corrected'];z['meta']=meta[stem];data[stem]=z
training=[data[r['stem']] for r in frames if meta[r['stem']]['role']=='training'];reserved=[data[r['stem']] for r in frames if meta[r['stem']]['role']!='training']
cells=np.unique(np.concatenate([z['cell'] for z in training]));nc=len(cells);lookup=np.full(NC*NC,-1);lookup[cells]=np.arange(nc);pc=3*(len(training)-1)
ii=[];yy=[];ww=[];PP=[];ss=[]
for j,z in enumerate(training):
    nr=len(z['g']);P=np.zeros((nr,pc))
    if j:P[:,3*(j-1):3*j]=np.stack([np.ones(nr),(z['x']-CX)/455,(z['y']-CY)/455],1)
    ii.append(lookup[z['cell']]);yy.append(z['g']);ww.append(1/(14.826313721285086*z['variance']));PP.append(P);ss.append(z['scatter'])
i=np.concatenate(ii);y=np.concatenate(yy);w=np.concatenate(ww);P=np.concatenate(PP);scatter=np.concatenate(ss);D=np.bincount(i,weights=w,minlength=nc);safe=np.maximum(D,1e-30);B=np.stack([np.bincount(i,weights=w*P[:,j],minlength=nc) for j in range(pc)],1);H=P.T@(w[:,None]*P)-B.T@(B/safe[:,None]);chol=cho_factor(H)
def template(y):
    b=np.bincount(i,weights=w*y,minlength=nc);planes=cho_solve(chol,P.T@(w*y)-B.T@(b/safe));return (b-B@planes)/safe,planes
models={name:template(y-c) for name,c in [('baseline',0.),('corrected',scatter)]}
np.savez_compressed(OUT/'A2_templates.npz',cells=cells,baseline=models['baseline'][0],corrected=models['corrected'][0]/(1-p.sum()))
results=[];sector_rows=[];profiles={}
for z in reserved:
    idx=lookup[z['cell']];valid=idx>=0;cal=valid&(z['radius']>=260)&(z['radius']<350);stem=z['meta']['stem'];g=z['g'];P=np.stack([np.ones(len(g)),(z['x']-CX)/455,(z['y']-CY)/455],1);weight=np.zeros(len(g));weight[valid]=1/(14.826313721285086*z['variance'][valid]+1/D[idx[valid]])
    residuals={};planes={}
    for name,(m,_) in models.items():
        pred=np.zeros(len(g));pred[valid]=m[idx[valid]]
        if name=='corrected':pred+=z['scatter']
        plane=np.linalg.lstsq(P[cal]*np.sqrt(weight[cal,None]),(g-pred)[cal]*np.sqrt(weight[cal]),rcond=None)[0];pred+=P@plane
        residuals[name]=g-pred;planes[name]=plane.tolist()
    reg=[]
    for label,use in [('face',(z['radius']>=350)&(z['radius']<415)),('wide_limb',(z['distance']>=-40)&(z['distance']<-6)),('last_six',(z['distance']>=-6)&(z['distance']<-.5))]:
        use &=valid
        mse={name:float(np.sum(weight[use]*rr[use]**2)/np.sum(weight[use])) for name,rr in residuals.items()}
        reg.append(dict(region=label,rows=int(use.sum()),mse=mse,reduction=1-mse['corrected']/mse['baseline']))
        for sector in range(12):
            use_sec=use&(np.floor(z['angle']/(np.pi/6)).astype(int)==sector)
            if not use_sec.any():continue
            sector_rows.append(dict(stem=stem,epoch=z['meta']['epoch'],region=label,sector=sector,rows=int(use_sec.sum()),weight=float(weight[use_sec].sum()),sse={k:float(np.sum(weight[use_sec]*v[use_sec]**2)) for k,v in residuals.items()}))
    results.append(dict(stem=stem,epoch=z['meta']['epoch'],planes=planes,regions=reg))
    np.savez_compressed(OUT/f'A2_reserved_{stem}.npz',**residuals,radius=z['radius'],distance=z['distance'],angle=z['angle'],weight=weight,cell=z['cell'])
epochs=[];sectors=[]
for epoch in sorted(set(r['epoch'] for r in sector_rows)):
    for region in ['face','wide_limb','last_six']:
        rows=[r for r in sector_rows if r['epoch']==epoch and r['region']==region];sse={k:sum(r['sse'][k] for r in rows) for k in models};epochs.append(dict(epoch=epoch,region=region,reduction=1-sse['corrected']/sse['baseline']))
        for sector in range(12):
            rs=[r for r in rows if r['sector']==sector];sse={k:sum(r['sse'][k] for r in rs) for k in models}
            if sse['baseline']>0:sectors.append(dict(epoch=epoch,region=region,sector=sector,ratio=sse['corrected']/sse['baseline']))
save('A2_reserved_result.json',dict(method=__doc__,p=p.tolist(),epochs=epochs,sectors=sectors,frames=results,interpretation='Conditional temporal prediction only. Does not prove removal of shared atmosphere or PSF uniqueness; independent telescope and photographic checks still pending.'))
fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
for ax,region in zip(axes,['face','wide_limb','last_six']):
    rows=[r for r in epochs if r['region']==region];ax.bar([r['epoch'].split('_')[1] for r in rows],[100*r['reduction'] for r in rows]);ax.axhline(0,c='k',lw=.7);ax.set(title=region,xlabel='Època reservada',ylabel='Reducció de residu (%)')
fig.suptitle('Model de dispersió congelat: predicció en preses reservades');fig.savefig(OUT/'A2_reserved_epochs.png',dpi=150)
print(json.dumps(epochs,ensure_ascii=False,indent=2),flush=True)
