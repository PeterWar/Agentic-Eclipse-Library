"""Read calibrated RGB witnesses; learn colour from cross-frame signal.
No single-frame PCA, no atlas fit, no new photograph. A diagnostic only.
"""
from pathlib import Path
import numpy as np,json
from scipy.fft import dctn,idctn
from scipy.ndimage import distance_transform_edt,gaussian_filter
from PIL import Image,ImageDraw
R=Path.cwd();O=R/'output/earthshine_spectral_broad_20260914';P=R/'output/earthshine_v50_causal_20260912'
y,x=np.mgrid[:1400,:1400];xx=(x-699.568111973117)/453.5;yy=(y-699.6475341408573)/453.5;r=np.hypot(xx,yy)*453.5;ang=np.arctan2(yy,xx)%(2*np.pi);sector=(ang*12/(2*np.pi)).astype(int)
mark=(x>=550)&(x<723)&(y>=902)&(y<1048);guard=(x>=500)&(x<773)&(y>=852)&(y<1098);fit=(r>80)&(r<330)&~guard&(sector%2==0);hold=(r>80)&(r<330)&~guard&(sector%2==1)
f=np.hypot((np.arange(1400)/(2*1400))[:,None],(np.arange(1400)/(2*1400))[None,:]);D=np.stack([np.ones(r.shape),xx,yy],-1)
stems=['572A2975','572A2993','572A2978','572A2996'];raw={};valid={};fft={}
for stem in stems:
 z=np.load(P/f'M0_camera_{stem}.npz');a=z['camera'].astype(float);valid[stem]=np.all(np.isfinite(a),axis=-1)
 for c in range(3):
  bad=~np.isfinite(a[...,c]);ix=distance_transform_edt(bad,return_distances=False,return_indices=True);a[...,c]=a[...,c][tuple(ix)]
 raw[stem]=a
 coeff=np.linalg.lstsq(D[fit],a[fit],rcond=None)[0];d=a-D@coeff
 fft[stem]=dctn(d,type=2,norm='ortho',axes=(0,1))
def band(stem,lo,hi):
 h=np.where((f>=1/hi)&(f<=1/lo),1.,0.)
 return idctn(fft[stem]*h[...,None],type=2,norm='ortho',axes=(0,1))
def corr(a,b,m):return float(np.corrcoef(a[m],b[m])[0,1])
rep=dict(method=__doc__,bands=[],spectral_models=[]);B={}
for lo,hi in [(16,32),(24,64),(64,128),(128,256)]:
 a=band(stems[2],lo,hi);b=band(stems[3],lo,hi);B[(lo,hi)]=(a,b)
 C=(a[fit].T@b[fit]+b[fit].T@a[fit])/(2*fit.sum());v,U=np.linalg.eigh(C);color=U[:,-1]/U[1,-1]
 correlations=[[corr(a[...,i],b[...,j],hold) for j in range(3)] for i in range(3)]
 rep['bands'].append(dict(band=[lo,hi],cross_covariance=C.tolist(),eigenvalues=v.tolist(),color=color.tolist(),heldout_channel_correlations=correlations));print(rep['bands'][-1],flush=True)

L=np.asarray(rep['bands'][1]['color']);S0=np.asarray(json.loads((P/'M1_spectral_falsifier.json').read_text())['solar_direction'])
# A temporal witness in another radial range; fixed plane subtraction removes
# broad atmospheric gradients, not a local lunar correction.
da=raw[stems[3]]-raw[stems[2]];smooth=gaussian_filter(da,(12,12,0));m=(r>330)&(r<425)&~guard&(sector%2==0)&valid[stems[2]]&valid[stems[3]]
plane=np.linalg.lstsq(D[m],smooth[m],rcond=None)[0];z=smooth-D@plane
S1=np.array([np.cov(z[...,c][m],z[...,1][m],bias=True)[0,1]/np.var(z[...,1][m]) for c in range(3)])
refs=np.load(R/'output/earthshine_broad_lroc_20260914/arrays/A6_reference_only.npz');Gref=np.load(R/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'].astype(float)
domain=r<420;good=(r>80)&(r<390)&~guard
def sm(v,s):return gaussian_filter(np.nan_to_num(v)*domain,s)/np.maximum(gaussian_filter(domain.astype(float),s),1e-9)
views={}
for name,S in [('exterior',S0),('temporal',S1)]:
 A=np.stack([L,S],-1);coef=np.linalg.pinv(A);maps={s:raw[s]@coef.T for s in stems};report=dict(name=name,lunar_color=L.tolist(),solar_color=S.tolist(),condition=float(np.linalg.cond(A)),third_channel_checks=[],comparisons=[])
 for leave in range(3):
  use=[c for c in range(3) if c!=leave];inv=np.linalg.inv(A[use]);ca=raw[stems[2]][...,use]@inv.T;cb=raw[stems[3]][...,use]@inv.T
  ra=sm(raw[stems[2]][...,leave]-ca@A[leave],12);rb=sm(raw[stems[3]][...,leave]-cb@A[leave],12)
  report['third_channel_checks'].append(dict(hold=leave,mark_residual=float(np.mean(ra[mark])),residual_corr=corr(ra,rb,hold),mark_variation_between_epochs=float(np.std((ra-rb)[mark]))))
 for lo,hi in [(8,32),(16,64),(32,96)]:
  a=(maps[stems[2]][...,0]+maps[stems[3]][...,0])/2;b=(raw[stems[2]][...,1]+raw[stems[3]][...,1])/2
  bb=sm(b,lo)-sm(b,hi);aa=sm(a,lo)-sm(a,hi)
  for key,q in [('DHS530',refs['DHS530']),('LROC',refs['LROC']),('Sony',Gref)]:
   rr=sm(q,lo)-sm(q,hi);d=dict(band=[lo,hi],reference=key)
   for tag,z in [('original_G',bb),('spectral_L',aa)]:
    gain=np.cov(z[good],rr[good],bias=True)[0,1]/np.var(z[good]);offset=np.mean(rr[good])-gain*np.mean(z[good]);res=(gain*z+offset-rr)/np.std(rr[good]);d[tag]=dict(corr=corr(z,rr,good),gain=float(gain),mark_bias=float(res[mark].mean()),mark_rms=float(np.sqrt(np.mean(res[mark]**2))))
   report['comparisons'].append(d);print(name,d,flush=True)
 views[name]=a
 rep['spectral_models'].append(report)
(O/'A1_cross_color.json').write_text(json.dumps(rep,indent=2)+'\n');np.savez_compressed(O/'arrays/A1_spectral_diagnostic.npz',**views,source_G=(raw[stems[2]][...,1]+raw[stems[3]][...,1])/2)
