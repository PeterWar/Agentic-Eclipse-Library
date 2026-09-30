"""Heldout radial-profile witness on measured native samples, no source editing.
Fit only deep Moon and immediate/exterior limb. Predict the intervening band
using either a Gaussian core or that core plus fixed 90mm pupil diffraction.
Independent training frames supply a common lunar residual; all other epochs
are validation. Profiles are sector means, not recovered lunar textures.
"""
from diffraction_common import *
from scipy.fft import fftfreq,ifft,fftshift
from scipy.optimize import least_squares
import time
meta={r['stem']:r for r in json.loads((NATIVE/'D1_inputs.json').read_text())['frames']}
frames=json.loads((OUT/'A2_stack_plan.json').read_text())['frames']
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
NS=12; STEP=.5;LO=-40.;HI=35.;NB=int((HI-LO)/STEP);d=LO+(np.arange(NB)+.5)*STEP
train=(d<=-27)|(d>=-3);held=(d>=-25)&(d<=-6)
L=4096;DX=.125;xx=(np.arange(L)-L//2)*DX;freq=fftfreq(L,d=DX)
save('B0_profile_plan.json',dict(method=__doc__,frames=[dict(stem=r['stem'],epoch=r['epoch'],role=meta[r['stem']]['role']) for r in frames],selection='Same 21 fully uncensored native fields; all valid native samples within -40..35px of the inherited observed contour',profiles=dict(sectors=NS,distance_bin=STEP,mean='Inverse native-variance mean; no interpolation of radiance',variance_inflation=14.826313721301643),training_distance='<=-27 or >=-3px relative to observed contour',heldout_distance='-25..-6px; no contribution to per-frame optical fit',parameters='Per frame/sector sigma[.4,3] and edge shift[-2,2]; four linear intensity/slope nuisances fitted on training distances only. Same parameter count for Gaussian and Airy models.',pupil='Nominal550nm fixed; measured scale;90mm; no fit to heldout halo',predictor='Physical one-dimensional line-spread Fourier response, square pixel aperture projected onto sector normal; core convolved with optional fixed pupil OTF',lunar_nuisance='Each model has its own common residual profile learned only from epochs vixen2/5; validation frames never enter it',gates='Each of six validation epochs improves weighted heldout MSE >=5%; >=75% sector/epoch scores do not worsen >2%; report boundary fits, this witness alone cannot qualify a photographic source',limits=['Broad sector averages ignore tangential brightness variation and curvature; this is a bounded hypothesis test','Inherited contour may retain registration errors; edge fits are not promoted to geometry','Shared calibration/FPN, not independent telescope corroboration','No output pixels created or modified']))
results=[]
for frame in frames:
    t0=time.time();stem=frame['stem'];z=np.load(SRC/f'A0_native_samples_{stem}.npz');x=z['x']-CX;y=z['y']-CY;r=np.hypot(x,y);ang=np.arctan2(y,x)%(2*np.pi);dist=r-np.interp(ang,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi);sec=np.floor(ang/(2*np.pi)*NS).astype(int);bi=np.floor((dist-LO)/STEP).astype(int);valid=z['valid']&(z['q']>0)&np.isfinite(z['g'])&np.isfinite(z['variance'])&(z['variance']>0)&(bi>=0)&(bi<NB);J=np.array(frame['J']);profiles=[]
    for s in range(NS):
        use=valid&(sec==s);ids=bi[use];w=1/z['variance'][use];sw=np.bincount(ids,weights=w,minlength=NB);cnt=np.bincount(ids,minlength=NB);g=np.bincount(ids,weights=w*z['g'][use],minlength=NB)/np.maximum(sw,1e-30);variance=14.826313721301643/np.maximum(sw,1e-30);ok=(cnt>=5)&np.isfinite(g);fit=ok&train;normal=np.array([np.cos((s+.5)*2*np.pi/NS),np.sin((s+.5)*2*np.pi/NS)])@J;pixel=np.sinc(freq*normal[0])*np.sinc(freq*normal[1]);fits={}
        assert fit.sum()>40,(stem,s,fit.sum())
        for name in ['gaussian','airy550']:
            pupil=np.ones_like(freq) if name=='gaussian' else airy_otf(abs(freq),550.)
            def design(params):
                sigma,shift=params;lsf=fftshift(ifft(pixel*pupil*np.exp(-2*np.pi**2*sigma*sigma*freq*freq)).real)/DX
                cdf=(np.cumsum(lsf)-.5*lsf)*DX;moment=(np.cumsum(xx*lsf)-.5*xx*lsf)*DX
                dd=d-shift;step=np.interp(dd,xx,cdf);ramp=dd*step-np.interp(dd,xx,moment)
                return np.stack([np.ones_like(d),d/30,step,ramp/30],axis=1)
            def solve(params,ret=False):
                A=design(params);ww=1/np.sqrt(variance[fit]);coef=np.linalg.lstsq(A[fit]*ww[:,None],g[fit]*ww,rcond=None)[0];pred=A@coef
                return (coef,pred) if ret else (pred[fit]-g[fit])*ww
            opt=least_squares(solve,[1.,0.],bounds=([.4,-2],[3.,2]),max_nfev=100,ftol=1e-8,xtol=1e-8,gtol=1e-8)
            coef,pred=solve(opt.x,True);fits[name]=dict(sigma=float(opt.x[0]),shift=float(opt.x[1]),coef=coef.tolist(),training_chi2=float(np.mean(solve(opt.x)**2)),boundary=bool(opt.x[0]<.401 or opt.x[0]>2.999 or abs(opt.x[1])>1.999),success=bool(opt.success),prediction=pred.tolist(),residual=(g-pred).tolist())
        profiles.append(dict(sector=s,count=cnt.tolist(),valid=ok.tolist(),mean=g.tolist(),variance=variance.tolist(),fits=fits))
    result=dict(stem=stem,role=meta[stem]['role'],epoch=frame['epoch'],profiles=profiles,seconds=time.time()-t0);results.append(result);save('B0_native_profiles.json',dict(method=__doc__,distance=d.tolist(),frames=results));print(stem,len(profiles),'sectors',round(time.time()-t0,2),'s',flush=True)
training=[r for r in results if r['role']=='training'];validation=[r for r in results if r['role']!='training'];rows=[];epochrows=[]
for name in ['gaussian','airy550']:
    nuisance=[]
    for s in range(NS):
        weights=np.array([np.array(r['profiles'][s]['valid'])/np.array(r['profiles'][s]['variance']) for r in training]);vals=np.array([r['profiles'][s]['fits'][name]['residual'] for r in training]);nuisance.append((weights*vals).sum(axis=0)/np.maximum(weights.sum(axis=0),1e-30))
    for epoch in sorted(set(r['epoch'] for r in validation)):
        er=[]
        for s in range(NS):
            err=[];ww=[]
            for row in validation:
                if row['epoch']!=epoch:continue
                p=row['profiles'][s];use=held&np.array(p['valid']);ee=np.array(p['fits'][name]['residual'])-nuisance[s];err.extend(ee[use]);ww.extend(1/np.array(p['variance'])[use])
            err=np.array(err);ww=np.array(ww);mse=float(np.sum(ww*err**2)/ww.sum());rrow=dict(operator=name,epoch=epoch,sector=s,mse_G2=mse,samples=len(err),weight=float(ww.sum()));rows.append(rrow);er.append(rrow)
        epochrows.append(dict(operator=name,epoch=epoch,mse_G2=sum(r['mse_G2']*r['weight'] for r in er)/sum(r['weight'] for r in er)))
comparisons=[];sectors=[]
for epoch in sorted(set(r['epoch'] for r in validation)):
    pair={r['operator']:r for r in epochrows if r['epoch']==epoch};reduction=1-pair['airy550']['mse_G2']/pair['gaussian']['mse_G2'];comparisons.append(dict(epoch=epoch,reduction_fraction=reduction,PASS=bool(reduction>=.05)))
    for s in range(NS):
        pair={r['operator']:r for r in rows if r['epoch']==epoch and r['sector']==s};ratio=pair['airy550']['mse_G2']/pair['gaussian']['mse_G2'];sectors.append(dict(epoch=epoch,sector=s,ratio=ratio,no_worse=bool(ratio<=1.02)))
save('B0_profile_witness.json',dict(method=__doc__,comparisons=comparisons,sectors=sectors,epoch_scores=epochrows,sector_scores=rows,boundary_fits={name:sum(p['fits'][name]['boundary'] for r in results for p in r['profiles']) for name in ['gaussian','airy550']},PASS=bool(all(r['PASS'] for r in comparisons) and np.mean([r['no_worse'] for r in sectors])>=.75),no_photographic_source=True))
print('DONE',comparisons,flush=True)
