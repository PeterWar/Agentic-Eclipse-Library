"""Predict Gaussian core widths in separate exposures from short-exposure fits.
Fixed training: Vixen 1/2000,1/1000,1/500; Sony1/800. Tests: 1/250..1/8
Vixen and1/100..1/30 Sony. No heldout widths tune the model. Profiles outside
the core-validity/rms qualification remain reported as failures, not filled.
"""
from optics_common import *
from scipy.optimize import least_squares
from scipy.special import ndtr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

data=json.loads((OUT/'A0_profiles.json').read_text())['frames'];z=np.load(OUT/'A0_profiles.npz');dist=z['distance'];use=(dist>=-18)&(dist<=18);x=dist[use]
records=[];models={};scored=[]
for train in ['vixen','sony']:
    learn=[];test=[]
    for m in data:
        if m['tren']!=train:continue
        islearn=(m['exp'] in [.0005,.001,.002]) if train=='vixen' else m['exp']==.00125
        istest=(.004<=m['exp']<=.125) if train=='vixen' else (.01<=m['exp']<=.034)
        for k,row in enumerate(m['sectors']):
            f=row['fit']
            good=f and f['success'] and not f['at_bound'] and f['relative_rms']<.03
            if islearn and good:learn.append((m,k,row))
            if istest:test.append((m,k,row,bool(good)))
    theta=np.deg2rad([r['angle'] for m,k,r in learn]);sig=np.array([r['fit']['sigma'] for m,k,r in learn]);A=np.stack([np.ones(len(theta)),np.cos(2*theta),np.sin(2*theta)],1)
    constant=float(np.median(sig));fit=least_squares(lambda p:A@p-sig**2,[constant**2,0,0],loss='soft_l1',f_scale=.3);p=fit.x
    assert p[0]>np.hypot(p[1],p[2]),'Indefinite ellipse'
    models[train]=dict(training_frames=sorted({m['stem'] for m,k,r in learn}),training_samples=len(learn),constant_sigma=constant,covariance_harmonics=p.tolist(),eigen_sigma=np.sqrt([p[0]-np.hypot(p[1],p[2]),p[0]+np.hypot(p[1],p[2])]).tolist(),training_sigma_quantiles=np.percentile(sig,[10,50,90]).tolist())
    for m,k,r,good in test:
        if not good:
            scored.append(dict(tren=train,stem=m['stem'],angle=r['angle'],qualified=False));continue
        yy=z['g'][m['profile_index'],k,use];noise=z['error'][m['profile_index'],k,use];f=r['fit'];amp=f['amplitude'];bg=f['inside_level'];yn=(yy-bg)/amp;err=np.maximum(noise/amp,.005)
        th=np.deg2rad(r['angle']);sp=float(np.sqrt(np.array([1,np.cos(2*th),np.sin(2*th)])@p))
        outcomes={}
        # Free centre, two backgrounds and brightness are nuisance parameters.
        # Width is predicted from other frames and cannot use the test fit.
        for name,s in [('constant',constant),('ellipse',sp)]:
            def pred(q):
                b,mi,step,dm,c=q;t=x-c;F=ndtr(t/s);phi=np.exp(-.5*(t/s)**2)/np.sqrt(2*np.pi)
                return b+mi*t+step*F+dm*(t*F+s*phi)
            fit2=least_squares(lambda q:(pred(q)-yn)/err,[0,0,1,0,0],bounds=([-1,-.2,.1,-.3,-8],[1,.2,5,.3,8]),loss='soft_l1',f_scale=2,max_nfev=150)
            outcomes[name]=dict(predicted_sigma=s,relative_rms=float(np.sqrt(np.mean((pred(fit2.x)-yn)**2))),center=float(fit2.x[4]))
        scored.append(dict(tren=train,stem=m['stem'],exp=m['exp'],time_C2=m['time_C2'],angle=r['angle'],qualified=True,free_sigma=f['sigma'],free_rms=f['relative_rms'],**outcomes))
    rows=[r for r in scored if r['tren']==train and r['qualified']]
    summary=dict(tren=train,test_total=len(test),test_qualified=len(rows),constant_sigma_error_median=float(np.median([abs(r['free_sigma']-r['constant']['predicted_sigma']) for r in rows])),ellipse_sigma_error_median=float(np.median([abs(r['free_sigma']-r['ellipse']['predicted_sigma']) for r in rows])),constant_profile_rms_median=float(np.median([r['constant']['relative_rms'] for r in rows])),ellipse_profile_rms_median=float(np.median([r['ellipse']['relative_rms'] for r in rows])),free_profile_rms_median=float(np.median([r['free_rms'] for r in rows])))
    records.append(summary);print(summary,flush=True)
save('A1_core_prediction.json',dict(method=__doc__,models=models,summary=records,tests=scored,limits=['Core only; broad wings and absolute scattered light not identified','Qualification uses a free-fit description and is reported explicitly; not an unseen discovery test','Long exposures lack a valid complete outer profile; extrapolation to them remains unproven','No photographic correction applied']))
(OUT/'vistes').mkdir(exist_ok=True)
fig,axs=plt.subplots(2,1,figsize=(11,7),layout='constrained')
for ax,train in zip(axs,['vixen','sony']):
    rows=[r for r in scored if r['tren']==train and r['qualified']]
    ax.scatter([r['angle'] for r in rows],[r['free_sigma']*2.35482 for r in rows],s=8,alpha=.3,label='Mesura en captures reservades')
    ang=np.linspace(0,360,400);p=np.array(models[train]['covariance_harmonics']);ss=np.sqrt(p[0]+p[1]*np.cos(np.deg2rad(2*ang))+p[2]*np.sin(np.deg2rad(2*ang)))
    ax.plot(ang,2.35482*ss,'k',label='Predicció des de captures curtes');ax.set(title=train,ylabel='FWHM del nucli observat (px finals)',xlabel='Angle (0° dreta;90° baix)');ax.legend(fontsize=8);ax.grid(alpha=.2)
fig.savefig(OUT/'vistes/A1_core_prediction.png',dpi=140)
