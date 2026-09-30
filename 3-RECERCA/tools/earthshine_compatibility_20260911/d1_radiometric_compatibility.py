"""Reference-guided HDR compatibility pilot: observed radiance, automatic weights.
No radius-dependent retouch, no intensity replacement, no image blur.
Noise variance is conditional and does not establish recovered lunar texture.
"""
from pathlib import Path
import sys,json,numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from f2_temporal import ng
from scipy.ndimage import gaussian_filter1d,gaussian_filter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=ROOT/'output/earthshine_compatibility_20260911';P=OUT/'source_pilot'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_COMPATIBILITY_20260911'
z=np.load(P/'source_arrays.npz');meta=json.loads((P/'source_inputs.json').read_text());names=meta['order']
g=np.array([z[n+'_g'] for n in names]);q=np.array([z[n+'_q'] for n in names]);v=np.array([z[n+'_variance'] for n in names]);weights=[]
for j,n in enumerate(names):
    valid=np.isfinite(g[j])&np.isfinite(v[j])&(v[j]>0)&(q[j]>0)
    vs,_=ng(v[j],valid,4.);weights.append(np.where(valid,q[j]/np.maximum(vs*meta['alpha'][n],1e-12),0))
w=np.array(weights);anchor=names.index('572A2976');ref=g[anchor]
gy,gx=np.gradient(np.nan_to_num(ref));geom_allowance=.3
sigma2=v+v[anchor]+geom_allowance**2*(gx*gx+gy*gy)
eligible=np.isfinite(ref)&(q[anchor]>.5)&(ref>0)
cy,cx=slice(25,52),slice(35,195);ys=np.arange(215,300)
def fuse(ww):return np.sum(ww*np.nan_to_num(g),axis=0)/np.maximum(ww.sum(0),1e-30)
base=fuse(w);results={'geometry_only':base};measures={};arrays={};fracs={}
for K in [3,5,8]:
    # Continuous source confidence from observed disagreement; no radial mask.
    significance2=(g-ref)**2/np.maximum(sigma2,1e-12)
    conf=1/(1+(significance2/(K*K))**2)
    conf=np.where(eligible[None]&np.isfinite(conf),conf,1);conf[anchor]=1
    ww=w*conf;key=f'K{K}';results[key]=fuse(ww);arrays[key+'_confidence']=conf;fracs[key]=ww/np.maximum(ww.sum(0),1e-30)
fracs['geometry_only']=w/np.maximum(w.sum(0),1e-30)
for key,im in results.items():
    core=im[cy,cx];diff=np.diff(np.log(np.maximum(core,1e-9)),axis=0);drop=1-np.exp(np.min(diff,axis=0));idx=np.argmin(diff,axis=0).astype(float)
    hp=idx-gaussian_filter1d(idx,5)
    measures[key]=dict(max_fractional_drop_median=float(np.median(drop)),edge_position_integer_highpass_rms=float(np.std(hp)),inner_difference_p95=float(np.percentile(abs(im[55:75,cx]-base[55:75,cx]),95)),fraction_1s_inner_median=float(np.median(fracs[key][names.index('572A2978'),55:75,cx])))
    arrays[key]=im
np.savez_compressed(OUT/'D1_compatibility_arrays.npz',**arrays)
rep=dict(method='Continuous reference-guided source compatibility using conditional photon/read noise and 0.3px registration allowance; anchor 2976 has measured unsaturated optical edge.',anchor='572A2976',nominal_K=5,sensitivity_K=[3,5,8],geometry_allowance_pixels=geom_allowance,measures=measures,limits=['Pilot on six-frame epoch with only three dominant frames newly registered','Unmodelled calibration and PSF systematics remain','A shorter reference may bias weak texture; cross-train validation is required','No replacement of observed intensities, no masks painted and no new PSB'])
(OUT/'D1_compatibility.json').write_text(json.dumps(rep,indent=2));print(json.dumps(measures,indent=2),flush=True)
fig,axs=plt.subplots(2,1,figsize=(12,7),layout='constrained')
for key,im in results.items():axs[0].plot(ys,im[:,115],label=key);axs[1].plot(ys,100*fracs[key][names.index('572A2978'),:,115],label=key)
axs[0].set(yscale='log',xlim=(243,280),ylim=(200,150000),ylabel='G lineal',title='Compatibilitat radiomètrica: pilot, sense PSB nou');axs[0].legend()
axs[1].set(xlim=(243,280),ylim=(-2,102),ylabel='Pes de la presa d’1 s (%)',xlabel='Fila local: exterior → interior lunar')
for ax in axs:ax.grid(alpha=.25)
fig.savefig(OUT/'vistes/D1_compatibility.png',dpi=140);plt.close(fig)
