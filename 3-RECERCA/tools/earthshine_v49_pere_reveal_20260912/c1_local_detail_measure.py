"""Measure the historical local-detail ablation; do not publish it as a repair."""
from reveal_common import *
from psd_tools import PSDImage
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
s=PSDImage.open(OUT/'C0_no_local_detail_camera_raw.psd')
l=next(l for l in s if l.name=='V45 font G · dos trens · preferència temporal · vel present')
raw=np.stack([channel(l,c) for c in range(3)],-1)
np.save(OUT/'C1_no_local_detail_CR_RGB16.npy',raw)
curves=json.loads((ROOT/'output/earthshine_validation_20260911/B1_global_tone_diagnostic.json').read_text())['curves']
mapped=[]
for image in [np.load(OUT/'B2_baseline_CR_RGB16.npy'),raw]:
    a=np.empty_like(image,dtype=float)
    for c,curve in enumerate(curves):
        f=PchipInterpolator([0.]+curve['input_DN16']+[65535.],[0.]+curve['output_DN16']+[65535.],extrapolate=False)
        a[...,c]=f(image[...,c])
    mapped.append(a.mean(-1))
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);angle=np.arctan2(y-CY,x-CX)%(2*np.pi)
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
d=r-np.interp(angle,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi)
delta=mapped[1]-mapped[0];offset=float(np.median(delta[r<350]));residual=delta-offset
rows=[]
for label,use in [('core',r<350),('inner_30_80',(d>=-80)&(d<-30)),('limb_6_25',(d>=-25)&(d<-6)),('last_3_inside',(d>=-3)&(d<0)),('outside_0_3',(d>=0)&(d<3))]:
    rows.append(dict(region=label,baseline_median_DN16=float(np.median(mapped[0][use])),no_detail_median_DN16=float(np.median(mapped[1][use])),normalized_delta_DN16=np.percentile(residual[use],[1,50,99]).tolist()))
hp=[a-gaussian_filter(a,2) for a in mapped]
contrast=[float(np.std(a[r<350])) for a in hp]
profile=[]
for lo in np.arange(-80,8,.5):
    use=(d>=lo)&(d<lo+.5)
    profile.append([float(lo+.25),float(np.median(mapped[0][use])),float(np.median(mapped[1][use]-offset))])
p=np.array(profile);fig,ax=plt.subplots(figsize=(9,4.5),layout='constrained')
ax.plot(p[:,0],p[:,1],label='Camera Raw històric, Textura 100 / Claredat 40')
ax.plot(p[:,0],p[:,2],label='Control 0 / 0, mediana de la cara igualada')
ax.axvline(0,c='k',lw=.7,ls=':');ax.legend(fontsize=8)
ax.set(xlabel='Distància a la vora observada (px)',ylabel='Lluminositat de pantalla (DN16)',title='Control causal de filtres de detall; no és una proposta estètica')
fig.savefig(OUT/'C1_local_detail_profiles.png',dpi=160);plt.close(fig)
save('C1_local_detail_result.json',dict(method=__doc__,global_median_response_DN16=offset,regions=rows,core_highpass_sigma2_std_DN16=contrast,core_highpass_std_ratio=contrast[1]/contrast[0],radial_profile=profile,limits=['Only historical CR descriptor; newest user filters are baked and not reconstructed','Core median matching is a diagnostic offset, not a correction to apply','Highpass standard deviation mixes real detail and noise; not a recovery metric','No new source, mask or PSB; disabling local detail is not automatically an accepted repair']))
print('CORE OFFSET',offset,'HIGH PASS STD RATIO',contrast[1]/contrast[0],flush=True)
print(json.dumps(rows,ensure_ascii=False,indent=2),flush=True)
