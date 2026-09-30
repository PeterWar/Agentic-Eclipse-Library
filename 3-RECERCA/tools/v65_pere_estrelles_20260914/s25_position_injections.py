from pathlib import Path
import numpy as np,json
from scipy.optimize import least_squares
from s4_native_psf import prf,X,Y,ann
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';rows=[]
for pre,manifest,models,names in [('S9','S9_native_manifest','S10_native_detection',['DSC06985','DSC06987','DSC06993']),('S11','S11_vixen_manifest','S13_vixen_detection',['572A2978','572A2982'])]:
 meta=json.loads((O/(manifest+'.json')).read_text());mo=json.loads((O/(models+'.json')).read_text())['models'];ids=[i for i,r in enumerate(meta['rows']) if r['kind']=='rotated_null'][::23][:8]
 for name in names:
  f=np.load(O/f'{pre}_{name}.npz')
  for j,i in enumerate(ids):
   mask=f['valid'][i]&((f['colour'][i]==1)|(f['colour'][i]==3));
   if mask.sum()<150:continue
   x=X[mask]/12;y=Y[mask]/12;B=np.c_[(f['colour'][i][mask]==1),(f['colour'][i][mask]==3),x,y,x*x,y*y,x*y].astype(float);z=f['data'][i][mask].astype(float);p=mo[name]['parameters'].copy();p[:2]=[(j*.37)%1-.5,(j*.61)%1-.5];tt=prf(p)[mask];D=np.c_[tt,B];q=np.linalg.lstsq(D,z,rcond=None)[0];res=z-D@q;noise=max(1.4826*np.median(abs(res[ann[mask]]-np.median(res[ann[mask]]))),.025);fe=noise*np.linalg.norm(np.linalg.pinv(D)[0]);
   for snr in [10,30,100]:
    flux=fe*snr;v=z+flux*tt
    def fun(delta,ret=False):
     pp=p.copy();pp[:2]=(np.array(p[:2])+delta).tolist();D=np.c_[prf(pp)[mask],B];q=np.linalg.lstsq(D,v,rcond=None)[0]
     return q if ret else (D@q-v)/noise
    sol=least_squares(fun,[.23,-.18],bounds=(-2,2),loss='soft_l1',f_scale=2,max_nfev=35);q=fun(sol.x,True);rows.append(dict(frame=name,index=i,SNR=snr,centroid_error_native=float(np.linalg.norm(sol.x)),flux_recovery_with_real_background=float(q[0]/flux)))
  print(name,flush=True)
summary={}
for snr in [10,30,100]:
 a=[r for r in rows if r['SNR']==snr];e=np.array([r['centroid_error_native'] for r in a]);f=np.array([r['flux_recovery_with_real_background'] for r in a]);summary[snr]=dict(n=len(a),position_median=float(np.median(e)),position_p95=float(np.quantile(e,.95)),position_max=float(e.max()),flux_median=float(np.median(f)),flux_p05_p95=np.quantile(f,[.05,.95]).tolist(),flux_within10pct=int(np.sum(abs(f-1)<=.1)))
(O/'S25_position_injections.json').write_text(json.dumps(dict(summary=summary,trials=rows,scope='Full noisy fit, real untouched CFA background. Discovery selection is separately frozen. Low-SNR uncertainty is retained.'),indent=2));print(summary)
