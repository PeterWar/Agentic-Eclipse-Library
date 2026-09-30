"""Blind-phase common-source transfer of frozen C0 compositor, exact fixed-weight
source-domain response. Signal is injected into each valid source's asinh G.
This excludes CFA calibration/registration/weight re-estimation and CameraRaw;
no end-to-end RAW transfer claim. No tuning follows these frozen phases.
"""
from validation_common import *
from scipy.fft import dctn,idctn
z=np.load(OUT/'C0_temporal_ensemble.npz');meta=json.loads((OUT/'C0_temporal_ensemble.json').read_text());GG=np.load(OUT/'ensemble_cache/G.npy',mmap_mode='r');WW=np.load(OUT/'ensemble_cache/W.npy',mmap_mode='r');pref=np.load(CAU45/'vixen_epoch_preference.npy',mmap_mode='r');da=z['den_all'];dp=z['den_preference'];base=z['base'];cand=z['candidate'];meanroot=np.zeros((N,N))
for i,row in enumerate(meta['source_frames']):
 w=WW[i].astype(float);m=.5*w/da+.5*w*pref[row['preference_index']]/dp;meanroot+=m*np.sqrt(GG[i].astype(float)**2+400)
uc=np.arcsinh(cand/20);ub=np.arcsinh(base/20);ug=np.arcsinh(z['gradient_candidate']/20)
lap=(2-2*np.cos(np.pi*np.arange(N)/N))[:,None]+(2-2*np.cos(np.pi*np.arange(N)/N))[None,:];a=1/64
f=np.hypot((np.arange(N)/(2*N))[:,None],(np.arange(N)/(2*N))[None,:]);q=np.clip((f-1/16)/(1/8-1/16),0,1);H=.5-.5*np.cos(np.pi*q)
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);rng=np.random.default_rng(114731);rows=[]
for scale in [8,16,24,40,64]:
 for angle in [.0,.57,1.19]:
  phase=float(rng.uniform(0,2*np.pi));sig=.002*np.sin(2*np.pi*(x*np.cos(angle)+y*np.sin(angle))/scale+phase)
  db=.5*(np.arcsinh((base*np.cosh(sig)+meanroot*np.sinh(sig))/20)-np.arcsinh((base*np.cosh(sig)-meanroot*np.sinh(sig))/20))
  # Exact gradient response of u_i +/- signal: Laplacian(signal).
  du_grad=idctn((lap*dctn(sig,type=2,norm='ortho')+a*dctn(db,type=2,norm='ortho'))/(lap+a),type=2,norm='ortho')
  du=db+idctn(dctn(du_grad-db,type=2,norm='ortho')*H,type=2,norm='ortho')
  reg=[]
  for lo,hi in [(0,350),(350,435),(435,454)]:
   m=(r>=lo)&(r<hi);gain=float(np.sum(du[m]*sig[m])/np.sum(sig[m]**2));err=float(np.sqrt(np.mean((du[m]-sig[m])**2)/np.mean(sig[m]**2)));reg.append(dict(radius=[lo,hi],gain=gain,relative_error=err,pass_90_110=.9<=gain<=1.1))
  rows.append(dict(scale=scale,angle=angle,phase=phase,regions=reg))
save('C4_compositor_transfer.json',dict(method=__doc__,seed=114731,amplitude_asinh=.002,rows=rows,PASS_operator_only=all(g['pass_90_110'] for row in rows for g in row['regions'])))
print('transfer minmax',min(g['gain'] for row in rows for g in row['regions']),max(g['gain'] for row in rows for g in row['regions']),flush=True)
