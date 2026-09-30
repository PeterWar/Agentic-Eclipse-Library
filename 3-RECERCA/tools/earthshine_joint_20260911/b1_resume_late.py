"""Converged continuation of the first fixed-parameter test of separate lunar and moving solar scenes.
Train each epoch on1/1000,1/250,1/60,1/4s. Reserve1/15s and1s completely
for prediction. Lambda10 is a declared diagnostic, not tuned to the heldouts.
No photographic output, no mask edit, no imported external texture.
"""
from forward_model import *
import time

fm=json.loads((SRC/'B1_full_native_ensemble.json').read_text())['source_frames'];GG=np.load(SRC/'compositor_cache/G.npy',mmap_mode='r');WW=np.load(SRC/'compositor_cache/W.npy',mmap_mode='r')
meta=json.loads((OPT/'B3_epoch_stationarity.json').read_text())['epochs'];sigma=json.loads((OPT/'A1_core_prediction.json').read_text())['models']['vixen']['constant_sigma'];rng=np.random.default_rng(114899)
meta=[e for e in meta if e['epoch']=='vixen_5']
reports=[e for e in json.loads((OUT/'B1_partial1600.json').read_text())['epochs'] if e['epoch']!='vixen_5'];y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY)
for ep in meta:
    epoch=ep['epoch'];rows=ep['frames'];ids=[next(i for i,m in enumerate(fm) if m['stem']==a['stem']) for a in rows];G=np.array([GG[i] for i in ids],dtype=float);W=np.array([WW[i] for i in ids],dtype=float);centres=np.array([a['solar_center_in_lunar_grid'] for a in rows])
    hold=np.array([np.isclose(a['exp'],1.) or np.isclose(a['exp'],1/15) for a in rows]);train=~hold;assert train.sum()==4 and hold.sum()==2
    # Exclude observations whose forward support would leave the fixed input
    # rectangle. This is physical operator support, not a lunar contour mask.
    margin=16;W[:,:margin]=0;W[:,-margin:]=0;W[:,:,:margin]=0;W[:,:,-margin:]=0
    model=JointScene(G[train],W[train],centres[train],sigma)
    print(epoch,'unknowns',model.size,'scales',model.ms,model.cs,'train',[a['stem'] for a,h in zip(rows,train) if h],flush=True)
    # Dot-product tests of the complete forward/adjoint including occultation,
    # bilinear solar motion, boundaries and radiance scaling.
    v=rng.normal(size=model.size);ys=[rng.normal(size=(N,N)) for _ in range(train.sum())]
    lhs=sum(np.sum(a*b) for a,b in zip(model.forward(v),ys));rhs=np.dot(v,model.adjoint(ys));gap=abs(lhs-rhs)/max(abs(lhs),abs(rhs),1)
    assert gap<1e-10,(epoch,gap)
    del v,ys
    checkpoint=OUT/f'B1_{epoch}_partial1600.npz'
    x0=None
    if checkpoint.exists():
        old=np.load(checkpoint);x0=model.pack(old['lunar']/model.ms,old['solar']/model.cs);old.close()
    start=time.time();v,fit=model.solve(10,x0=x0,maxiter=600,rtol=3e-7);fit['seconds']=time.time()-start;fit['previous_iterations']=1600;fit['warm_start']=str(checkpoint) if checkpoint.exists() else None
    m,c=model.unpack(v);M=m*model.ms;C=c*model.cs;pred_train=model.forward(v)
    # Predict reserved exposures with the same scene and prescribed solar
    # transforms. No parameter is fitted to these exposures.
    tests=[];saved={}
    den=np.sum(W[train],0);static=np.sum(W[train]*G[train],0)/np.maximum(den,1e-30)
    for i,(row,h) in enumerate(zip(rows,hold)):
        t=Warp(*(centres[i]-model.reference)[::-1]);moving=model.conv(model.P*M+model.Q*t.forward(C))
        stationary=model.conv(model.P*M+model.Q*C)
        regions=[]
        for lo,hi in [(0,350),(350,435),(435,449),(449,454),(454,480),(500,650)]:
            good=(W[i]>0)&(den>0)&(r>=lo)&(r<hi)
            if good.sum()<100:continue
            measures={}
            for name,pred in [('joint_moving',moving),('same_scene_no_motion',stationary),('static_HDR',static)]:
                rr=W[i][good]*(pred[good]-G[i][good])**2;measures[name]=dict(mean_effective_residual=float(np.mean(rr)),quantiles=np.percentile(rr,[50,90,99]).tolist())
            regions.append(dict(radius=[lo,hi],pixels=int(good.sum()),**measures))
        tests.append(dict(stem=row['stem'],exp=row['exp'],held_out=bool(h),regions=regions))
        if h:saved[row['stem']+'_prediction']=moving;saved[row['stem']+'_observed']=G[i];saved[row['stem']+'_weight']=W[i]
    active=model.P>0;stats=[]
    for lo,hi in [(0,350),(350,435),(435,449),(449,454)]:
        good=active&(r>=lo)&(r<hi);stats.append(dict(radius=[lo,hi],pixels=int(good.sum()),negative=int((M[good]<0).sum()),quantiles=np.percentile(M[good],[0,1,50,99,100]).tolist()))
    np.savez_compressed(OUT/f'B1_{epoch}_joint.npz',lunar=M,solar=C,occlusion=model.P,solar_support=model.cm,static_training_HDR=static,solar_reference=model.reference,**saved)
    report=dict(epoch=epoch,train_frames=[a['stem'] for a,h in zip(rows,train) if h],heldout_frames=[a['stem'] for a,h in zip(rows,hold) if h],adjoint_relative_error=float(gap),fit=fit,scales=dict(lunar=model.ms,solar=model.cs),short_core_sigma=sigma,forward_sigma=model.sigma,internal_occlusion='Measured Vixen optical silhouette,4x4 area quadrature, never a PSB mask change',lunar_statistics=stats,tests=tests)
    reports.append(report);save('B1_joint_converged.json',dict(method=__doc__,epochs=reports,status='DIAGNOSTIC only; scientific/final photographic PASS not established',limits=['Remapped source-domain approximation, not native CFA likelihood','Gaussian core and silhouette remain model assumptions','Fixed lambda10; no hyperparameter or PSF uncertainty validation yet','No positivity clipping, no new product or manual contour']))
    print(epoch,'FIT',fit,'INNER_NEGATIVE',sum(s['negative'] for s in stats),flush=True)
    if fit['cg_info']!=0 or max(fit['block_relative_residuals'].values())>1e-5:raise RuntimeError('Solver not qualified; keep diagnostic and do not interpret as recovered detail')
    del model,G,W,M,C,saved,v,m,c,pred_train
print('DONE',flush=True)
