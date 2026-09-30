"""Judge the combined epoch model on four unchanged heldout exposures.
Use exactly the common physically valid footprint for all compared predictions.
Counts distinguish fully lunar pixels from mixed limb pixels. No clipping.
"""
from joint_common import *
from scipy.ndimage import gaussian_filter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

e=json.loads((OUT/'B3_joint_epochs.json').read_text())['epochs'][0]
assert e['fit']['cg_info']==0 and max(e['fit']['block_relative_residuals'].values())<1e-5
z=np.load(OUT/'B3_vixen_2_5_joint.npz');P=z['occlusion'];M=z['lunar'];base=z['static_training_HDR'];covered=z['training_coverage'];smooth=gaussian_filter(base,e['forward_sigma'],mode='reflect')
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY)
oldmeta=json.loads((OUT/'B1_joint_converged.json').read_text())['epochs'];old={a['epoch']:np.load(OUT/f"B1_{a['epoch']}_joint.npz") for a in oldmeta}
tests=[]
for h in e['tests']:
    if not h['held_out']:continue
    stem=h['stem'];oe=next(a for a in oldmeta if stem in a['heldout_frames']);o=old[oe['epoch']]
    g=z[stem+'_observed'];w=z[stem+'_weight'];pred=z[stem+'_prediction'];prior=o[stem+'_prediction'];support=(w>0)&(o[stem+'_weight']>0)&covered
    assert np.array_equal(g[support],o[stem+'_observed'][support])
    regions=[]
    for lo,hi in [(0,350),(350,435),(435,449),(449,454),(454,480),(500,650)]:
        good=support&(r>=lo)&(r<hi)
        if good.sum()<100:continue
        measures={}
        for name,p in [('joint_epochs',pred),('separate_epoch',prior),('static_HDR8',base),('fixed_smoothing',smooth)]:
            d=p[good]-g[good];rr=w[good]*d*d
            measures[name]=dict(mean_effective_residual=float(rr.mean()),median_signed_error_G=float(np.median(d)),abs_error_G_quantiles=np.percentile(abs(d),[50,90,99]).tolist())
        regions.append(dict(radius=[lo,hi],pixels=int(good.sum()),**measures))
    tests.append(dict(stem=stem,exp=h['exp'],regions=regions))
stats=[]
for name,good in [('all_lunar',P>0),('fully_lunar',P>.999),('mixed_limb',(P>0)&(P<=.999)),('inner435_449',(P>0)&(r>=435)&(r<449))]:
    stats.append(dict(region=name,pixels=int(good.sum()),negative=int((M[good]<0).sum()),radiance_quantiles=np.percentile(M[good],[0,1,50,99,100]).tolist()))
save('B4_joint_epochs_review.json',dict(method=__doc__,fit=e['fit'],heldout=tests,lunar_statistics=stats,status='Source diagnostic only; no independent telescope recovery or photographic PASS established',changes_from_B1=['Shared lunar and solar scenes across early and late epoch;8 training frames and4 heldouts','Numerically converged pixel-area occultation instead of coarse4x4 sampling','Lambda scaled20 for8 frames, preserving lambda per frame10/4; not tuned to holdouts'],limits=['Cannot attribute any change uniquely to joint epochs versus the numerical area correction','Same-telescope heldouts are predictive controls, not independent-sensor corroboration','Calibration, registration, weights and geometry are inherited from the earlier chain; heldout scope is the new scene fit, not an end-to-end RAW calibration test','Measured optical silhouette and Gaussian core remain physical assumptions; no broad PSF wings']))
fig,ax=plt.subplots(1,3,figsize=(15,5),constrained_layout=True);cmap=plt.get_cmap('gray').copy();cmap.set_under('#d14a61');cmap.set_bad('#26384c')
for k,(a,title) in enumerate([(base,'HDR estàtic · 8 preses d’ajust'),(M,'Lluna comuna · C2 i C3')]):
    ax[k].imshow(np.arcsinh(np.where(P>0,a,np.nan)/500),vmin=0,vmax=np.arcsinh(2500/500),cmap=cmap,interpolation='nearest');ax[k].set_title(title)
ax[2].imshow(np.where(P>0,(M<0).astype(float),np.nan),cmap='Reds',vmin=0,vmax=1,interpolation='nearest');ax[2].set_title(f"{((M<0)&(P>0)).sum():,} píxels negatius")
for a in ax:a.set_xlim(220,1180);a.set_ylim(1180,220);a.axis('off')
fig.suptitle('Model conjunt: fonts lineals sense Camera Raw; diagnòstic, no nou PSB')
fig.savefig(OUT/'vistes/B4_joint_epochs.png',dpi=140);plt.close(fig)
for h in tests:print(h['stem'],[(a['radius'],round(a['joint_epochs']['mean_effective_residual']/a['separate_epoch']['mean_effective_residual'],3),round(a['joint_epochs']['mean_effective_residual']/a['static_HDR8']['mean_effective_residual'],3)) for a in h['regions']],flush=True)
print('LUNAR',stats,flush=True)
