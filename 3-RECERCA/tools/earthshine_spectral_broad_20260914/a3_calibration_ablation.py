"""Read-only scientific ablations of spatial calibration and observed weights.

Eight >=1-second Vixen frames, no new registration. Disabling a calibration is
not a proposed correction: this tests whether its spatial fingerprint can
plausibly explain the broad marked feature. No reference fits a pixel delta.
"""
from pathlib import Path
import json,numpy as np,cv2
from astropy.io import fits
from scipy.ndimage import gaussian_filter
R=Path.cwd();O=R/'output/earthshine_spectral_broad_20260914';OLD=R/'output/earthshine_max_detail_20260913'
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_SPECTRAL_BROAD_20260914'
rows=[q for q in json.loads((OLD/'A1_native_rgb_all.json').read_text())['frames'] if q['tren']=='vixen' and q['exp']>=1]
CAL=Path('/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/019_VIXEN_CIENCIA_20260827T212404Z/0-calibracio')
# OpenCV expects native byte order; FITS arrays are big-endian on disk.
flat=fits.getdata(CAL/'FLAT_RADIAL.fits').astype(np.float32);darks={e:fits.getdata(CAL/f'masters_dark/MD_E{e:g}s.fits').astype(np.float32) for e in [1,2,10]}
y,x=np.mgrid[:1400,:1400];rad=np.hypot(x-699.568111973117,y-699.6475341408573)
domain=rad<420;mark=(x>=550)&(x<723)&(y>=902)&(y<1048);guard=(x>=500)&(x<773)&(y>=852)&(y<1098)
use=(rad>80)&(rad<390)&~guard;den=np.zeros(rad.shape);num={k:np.zeros(rad.shape) for k in ['baseline','without_spatial_flat','without_spatial_dark','constant_precision']};cd=np.zeros(rad.shape)
diagnostics=[]
def sm(a,s):return gaussian_filter(np.where(domain,a,0),s)/np.maximum(gaussian_filter(domain.astype(float),s),1e-10)
for meta in rows:
 z=np.load(OLD/'native'/f"vixen_{meta['stem']}.npz");A=np.array(meta['roi_to_native']);nx=(A[0,0]*x+A[0,1]*y+A[0,2]);ny=(A[1,0]*x+A[1,1]*y+A[1,2]);n=np.zeros(rad.shape);vq=np.zeros(rad.shape);sq=np.zeros(rad.shape);nflat=np.zeros(rad.shape);ndark=np.zeros(rad.shape)
 field=[]
 for channel in ['G1','G2']:
  q=z[channel+'_q'].astype(float);a=np.nan_to_num(z[channel]).astype(float);v=np.nan_to_num(z[channel+'_var']).astype(float)
  cov=next(c for c in meta['coverage'] if c['channel']==channel);origin=cov['native_origin'];ox=origin[0]%2;oy=origin[1]%2
  mx=((nx-ox)/2).astype('float32');my=((ny-oy)/2).astype('float32')
  ff=cv2.remap(flat[oy::2,ox::2],mx,my,cv2.INTER_LINEAR).astype(float)
  dark=darks[meta['exp']][oy::2,ox::2];dd=cv2.remap(dark,mx,my,cv2.INTER_LINEAR).astype(float)
  assert np.all((ff[domain]>.5)&(ff[domain]<1.5))
  assert np.all((dd[domain]>400)&(dd[domain]<3000))
  constant=float(np.median(dd[rad<350]));delta_dark=(dd-constant)*meta['k']*meta['WB'][1]/np.maximum(ff,1e-9)/meta['exp']
  off=meta['offset_RGB'][1]
  n+=q*a;vq+=q*q*v;sq+=q;nflat+=q*((a-off)*ff+off);ndark+=q*(a+delta_dark)
  field.append([float(np.median(ff[mark])),float(np.ptp(ff[mark])),float(np.std(sm(delta_dark,16)[mark]))])
 a=n/np.maximum(sq,1e-30);var=vq/np.maximum(sq*sq,1e-30);good=(sq>0)&domain
 vs=gaussian_filter(np.where(good,var,0),4)/np.maximum(gaussian_filter(good.astype(float),4),1e-30)
 w=np.where(good,(sq/2)/np.maximum(vs,1e-12),0);c=np.where(good,(sq/2)/float(np.median(vs[use&good])),0)
 den+=w;cd+=c;num['baseline']+=w*a;num['without_spatial_flat']+=w*nflat/np.maximum(sq,1e-30);num['without_spatial_dark']+=w*ndark/np.maximum(sq,1e-30);num['constant_precision']+=c*a
 diagnostics.append(dict(stem=meta['stem'],exp=meta['exp'],flat_dark_mark=field,mark_min_quality=float(np.min(sq[mark])/2)))
 print(meta['stem'],diagnostics[-1],flush=True)
arr={k:v/np.maximum(cd if k=='constant_precision' else den,1e-30) for k,v in num.items()}
arr['Gclean']=np.load(R/'output/earthshine_v56_three_routes_20260913/arrays/R5_sources.npz')['Gclean'];arr['Sony']=np.load(R/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference']
ref=np.load(R/'output/earthshine_broad_lroc_20260914/arrays/A6_reference_only.npz');comparisons=[]
for sig in [(8,32),(16,64),(32,96)]:
 b={k:sm(np.nan_to_num(v),sig[0])-sm(np.nan_to_num(v),sig[1]) for k,v in arr.items()}
 for name in ['without_spatial_flat','without_spatial_dark','constant_precision']:
  d=b[name]-b['baseline'];print('EFFECT',sig,name,'mark',np.percentile(d[mark],[0,50,100]),'sourceDN',flush=True)
  comparisons.append(dict(type='effect',sigmas=sig,name=name,mark_delta_source_DN=np.percentile(d[mark],[0,50,100]).tolist(),control_delta_rms=float(np.std(d[use]))))
 for key in ['Sony','DHS530','LROC']:
  a=b['Sony'] if key=='Sony' else sm(ref[key],sig[0])-sm(ref[key],sig[1]);v=b['baseline'];gain=np.cov(v[use],a[use],bias=True)[0,1]/np.var(v[use]);offset=a[use].mean()-gain*v[use].mean();sd=a[use].std()
  for name,v in b.items():
   if name=='Sony':continue
   d=(gain*v+offset-a)/sd;item=dict(type='comparison',sigmas=sig,name=name,reference=key,fixed_gain=float(gain),mark_bias=float(np.mean(d[mark])),mark_rms=float(np.sqrt(np.mean(d[mark]**2))),control_rms=float(np.sqrt(np.mean(d[use]**2))))
   comparisons.append(item)
   if sig==(16,64):print(item,flush=True)
np.savez_compressed(O/'arrays/A3_calibration_ablation.npz',**{k:v.astype('float32') for k,v in arr.items()})
(O/'A3_calibration_ablation.json').write_text(json.dumps(dict(method=__doc__,frames=diagnostics,comparisons=comparisons,status='COUNTERFACTUAL_ONLY_NOT_A_CORRECTION'),indent=2)+'\n')
