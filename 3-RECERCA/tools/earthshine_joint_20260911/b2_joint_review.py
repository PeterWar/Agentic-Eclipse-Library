"""Review the converged prototype against untouched held-out observations.
The blurred static HDR is a fixed smoothing control, not a proposed product.
No source-domain image or photographic layer is changed by these plots.
"""
from joint_common import *
from scipy.ndimage import gaussian_filter,map_coordinates
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

report=json.loads((OUT/'B1_joint_converged.json').read_text())
assert len(report['epochs'])==2
fm=json.loads((SRC/'B1_full_native_ensemble.json').read_text())['source_frames']
WW=np.load(SRC/'compositor_cache/W.npy',mmap_mode='r')
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY)
rows=[];fig,ax=plt.subplots(2,3,figsize=(15,10),constrained_layout=True)
cmap=plt.get_cmap('gray').copy();cmap.set_under('#d14a61');cmap.set_bad('#26384c')
for j,e in enumerate(report['epochs']):
    assert e['fit']['cg_info']==0 and max(e['fit']['block_relative_residuals'].values())<1e-5
    z=np.load(OUT/f"B1_{e['epoch']}_joint.npz")
    M=z['lunar'];P=z['occlusion'];base=z['static_training_HDR'];smooth=gaussian_filter(base,e['forward_sigma'],mode='reflect')
    ids=[next(i for i,m in enumerate(fm) if m['stem']==s) for s in e['train_frames']]
    covered=np.sum(WW[ids],axis=0)>0
    covered[:16]=False;covered[-16:]=False;covered[:,:16]=False;covered[:,-16:]=False
    checks=[]
    for h in e['tests']:
        if not h['held_out']:continue
        stem=h['stem'];g=z[stem+'_observed'];w=z[stem+'_weight'];pred=z[stem+'_prediction']
        regions=[]
        for row in h['regions']:
            lo,hi=row['radius'];good=(w>0)&covered&(r>=lo)&(r<hi)
            # The four training observations cover all these lunar bands.
            # Keep the exact original judging support for other regions too.
            assert int(good.sum())==row['pixels'],(stem,row['radius'],good.sum(),row['pixels'])
            q=w[good]*(smooth[good]-g[good])**2
            regions.append(dict(radius=[lo,hi],pixels=int(good.sum()),static_HDR=row['static_HDR']['mean_effective_residual'],joint_moving=row['joint_moving']['mean_effective_residual'],fixed_smoothing_control=float(q.mean())))
        checks.append(dict(stem=stem,exp=h['exp'],regions=regions))
    delta=None
    old=OUT/f"B0_{e['epoch']}_joint.npz"
    if old.exists():
        b0=np.load(old);good=P>0;d=M[good]-b0['lunar'][good]
        delta=dict(initial_iterations=650,absolute_lunar_delta_quantiles=np.percentile(abs(d),[50,90,99,100]).tolist());b0.close()
    rows.append(dict(epoch=e['epoch'],fit=e['fit'],heldout=checks,lunar_statistics=e['lunar_statistics'],total_lunar_negative=int(((M<0)&(P>0)).sum()),continuation_delta=delta))
    for k,(a,title) in enumerate([(base,'HDR de les quatre preses d’ajust'),(M,'Camp lunar inferit; vermell = negatiu')]):
        masked=np.where(P>0,a,np.nan)
        ax[j,k].imshow(np.arcsinh(masked/500),vmin=0,vmax=np.arcsinh(2500/500),cmap=cmap,interpolation='nearest')
        ax[j,k].set_xlim(220,1180);ax[j,k].set_ylim(1180,220);ax[j,k].set_title(e['epoch']+' · '+title);ax[j,k].axis('off')
    negative=(M<0)&(P>0)
    ax[j,2].imshow(np.where(P>0,negative.astype(float),np.nan),cmap='Reds',vmin=0,vmax=1,interpolation='nearest')
    ax[j,2].set_xlim(220,1180);ax[j,2].set_ylim(1180,220);ax[j,2].set_title(f"{negative.sum():,} píxels lunars negatius");ax[j,2].axis('off')
    z.close()
v=OUT/'vistes';v.mkdir(exist_ok=True)
fig.suptitle('Prototip físic: diagnòstic de fonts lineals, sense Camera Raw ni retoc del contorn',fontsize=15)
fig.savefig(v/'B2_joint_sources.png',dpi=140);plt.close(fig)

fig,ax=plt.subplots(2,4,figsize=(16,7),constrained_layout=True)
dist=np.arange(425,456,.25)
for j,e in enumerate(report['epochs']):
    z=np.load(OUT/f"B1_{e['epoch']}_joint.npz")
    for k,theta in enumerate([0,90,180,270]):
        t=np.deg2rad(theta);co=np.array([CY+dist*np.sin(t),CX+dist*np.cos(t)])
        p=map_coordinates(z['occlusion'],co,order=1)>0.99
        for key,label in [('static_training_HDR','HDR'),('lunar','Model lunar')]:
            a=map_coordinates(z[key],co,order=1);a[~p]=np.nan
            ax[j,k].plot(dist,a,label=label,lw=1.3)
        ax[j,k].axhline(0,c='black',lw=.6);ax[j,k].set_yscale('symlog',linthresh=500);ax[j,k].set_title(f"{e['epoch']} · {theta}°");ax[j,k].set_xlabel('Radi en píxels de la graella font');ax[j,k].grid(alpha=.2)
    ax[j,0].set_ylabel('Radiància G lineal');ax[j,0].legend()
    z.close()
fig.savefig(v/'B2_joint_profiles.png',dpi=140);plt.close(fig)
save('B2_joint_review.json',dict(method=__doc__,epochs=rows,status='Diagnostic only; negative radiance and heldout mismatch must not be hidden by clipping',limits=['Effective weights are not a calibrated independent-noise chi-square','The smoothing control only checks whether quieter interior residuals require scene separation','Heldout exposures come from the same telescope; no cross-sensor recovery claim']))
for e in rows:
    print(e['epoch'],'negative',sum(s['negative'] for s in e['lunar_statistics']))
    for h in e['heldout']:
        print(h['stem'],[(a['radius'],round(a['joint_moving']/a['static_HDR'],3),round(a['fixed_smoothing_control']/a['static_HDR'],3)) for a in h['regions']])
