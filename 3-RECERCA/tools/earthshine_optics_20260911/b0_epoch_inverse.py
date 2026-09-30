"""Bounded inverse-core pilot on two independent temporal Vixen HDR brackets.
Use the measured short-frame core, full Cartesian rectangle and fixed existing
source weights. Laplacian Tikhonov strength is set by the declared effective
noise discrepancy, never a painted region or detail judge. No PSB output.
"""
from optics_common import *
from scipy.fft import dctn,idctn
from scipy.sparse.linalg import LinearOperator,cg
from scipy.ndimage import gaussian_filter
import time

fm=json.loads((SRC/'B1_full_native_ensemble.json').read_text())['source_frames']
GG=np.load(SRC/'compositor_cache/G.npy',mmap_mode='r');WW=np.load(SRC/'compositor_cache/W.npy',mmap_mode='r')
models=json.loads((OUT/'A1_core_prediction.json').read_text())['models'];sigma=models['vixen']['constant_sigma']
f=np.arange(N)/(2*N);freq2=f[:,None]**2+f[None,:]**2;H=np.exp(-2*np.pi**2*sigma**2*freq2)
lap=(4*np.sin(np.pi*f)**2)[:,None]+(4*np.sin(np.pi*f)**2)[None,:];L2=lap**2
def conv(a):return idctn(dctn(a,type=2,norm='ortho')*H,type=2,norm='ortho')
def penalty(a):return idctn(dctn(a,type=2,norm='ortho')*L2,type=2,norm='ortho')
reports=[]
for epoch in ['vixen_2','vixen_5']:
    selected=[i for i,m in enumerate(fm) if m['epoch']==epoch];assert len(selected)==6
    den=np.zeros((N,N));num=den.copy()
    for i in selected:den+=WW[i];num+=WW[i].astype(float)*GG[i]
    assert np.all(den>0)
    g=num/den;scale=float(np.median(den));w=den/scale;rhs=conv(w*g);trace=[]
    cache=OUT/'solver_cache';cache.mkdir(exist_ok=True)
    # Effective noise includes pre-existing FPN factors. This is a conservative
    # operator discrepancy criterion, not a claim of calibrated chi-square.
    def solve(lam,x0=None):
        checkpoint=cache/f'{epoch}_{lam:.9g}.npz'
        if checkpoint.exists():
            zz=np.load(checkpoint);row=json.loads(checkpoint.with_suffix('.json').read_text());assert row['sigma']==sigma
            trace.append({**row,'cache_reused':True});print(epoch,'REUSED',lam,flush=True)
            return zz['inverse'],row['effective_noise_discrepancy']
        start=time.time();steps=[0]
        def mv(v):
            a=v.reshape(N,N);return (conv(w*conv(a))+lam*penalty(a)).ravel()
        # Symmetric two-level preconditioner: variable data weight dominates
        # smooth modes, Laplacian regularisation dominates fine modes. This
        # changes only convergence, not the stated quadratic objective.
        low=np.exp(-2*np.pi**2*4.**2*freq2);Q=low/H
        pre=(1-low**2)/(float(np.mean(w))*H**2+lam*L2)
        def pc(v):
            vh=dctn(v.reshape(N,N),type=2,norm='ortho')
            sm=idctn(vh*Q,type=2,norm='ortho')/w
            return idctn(dctn(sm,type=2,norm='ortho')*Q+vh*pre,type=2,norm='ortho').ravel()
        op=LinearOperator((N*N,N*N),matvec=mv,dtype=np.float64);M=LinearOperator(op.shape,matvec=pc,dtype=np.float64)
        def cb(v):
            steps[0]+=1
            if steps[0]%300==0:print(epoch,'CG',lam,steps[0],flush=True)
        answer,info=cg(op,rhs.ravel(),x0=(g if x0 is None else x0).ravel(),M=M,rtol=2e-6,atol=0,maxiter=1200,callback=cb)
        a=answer.reshape(N,N);res=conv(a)-g;discrepancy=float(np.mean(den*res**2));normal=float(np.linalg.norm(mv(answer)-rhs.ravel())/np.linalg.norm(rhs))
        row=dict(lambda_normalized=float(lam),effective_noise_discrepancy=discrepancy,cg_info=int(info),iterations=steps[0],normal_relative_residual=normal,seconds=round(time.time()-start,2));trace.append(row);print(epoch,row,flush=True)
        assert info==0 and normal<3e-6,row
        row['sigma']=sigma
        np.savez_compressed(checkpoint,inverse=a)
        checkpoint.with_suffix('.json').write_text(json.dumps(row,indent=2))
        return a,discrepancy
    # Find the bracket first, then at most six log-space steps. No image-based
    # adjustment of the chosen target (unit effective-noise discrepancy).
    lam=.01;a,d=solve(lam);lower=upper=None;best=(lam,a,d)
    for j in range(7):
        if .95<=d<=1.05:best=(lam,a,d);break
        if d<1:lower=(lam,a,d);lam*=10
        else:upper=(lam,a,d);lam/=10
        if lower and upper:break
        a,d=solve(lam,a)
        if abs(np.log(d))<abs(np.log(best[2])):best=(lam,a,d)
    if not .95<=best[2]<=1.05:
        assert lower and upper,('Discrepancy not bracketed',trace)
        for j in range(6):
            lam=np.sqrt(lower[0]*upper[0]);a,d=solve(lam,best[1]);item=(lam,a,d)
            if abs(np.log(d))<abs(np.log(best[2])):best=item
            if d<1:lower=item
            else:upper=item
            if .95<=d<=1.05:break
    lam,a,d=best;blur=conv(a);yy,xx=np.mgrid[:N,:N];r=np.hypot(xx-CX,yy-CY)
    stats=[]
    for lo,hi in [(0,350),(350,435),(435,454),(454,480)]:
        m=(r>=lo)&(r<hi);stats.append(dict(radius=[lo,hi],baseline_quantiles=np.percentile(g[m],[0,1,50,99,100]).tolist(),inverse_quantiles=np.percentile(a[m],[0,1,50,99,100]).tolist(),negative_pixels=int((a[m]<0).sum())))
    np.savez_compressed(OUT/f'B0_{epoch}_inverse.npz',baseline=g,inverse=a,reconvolved=blur,weight=den,psf_sigma=sigma,lambda_normalized=lam)
    reports.append(dict(epoch=epoch,frames=[fm[i]['stem'] for i in selected],sigma=sigma,lambda_normalized=float(lam),effective_noise_discrepancy=d,trace=trace,regions=stats,status='EXPERIMENTAL; no independent texture or halo PASS'))
    save('B0_epoch_inverse.json',dict(method=__doc__,epochs=reports,limits=['Core Gaussian measured only in short exposures; 1s extrapolation remains a hypothesis','Temporal HDR source uses existing mapping and weights; not a joint time-varying forward scene','No positivity clamp or new spatial mask','Originals and V48 untouched']))
print('DONE',flush=True)
