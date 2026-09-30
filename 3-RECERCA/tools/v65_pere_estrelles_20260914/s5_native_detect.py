from pathlib import Path
import numpy as np,json
from s4_native_psf import prf,X,Y
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';meta=json.loads((O/'S3_native_manifest.json').read_text());psf=json.loads((O/'S4_native_psf.json').read_text());ann=np.hypot(X,Y)>8;pars={};records=[];preds={}
for fr in meta['frames']:
 name=fr['name'];f=np.load(O/f'S3_{name}.npz');good=[r for r in psf if r['frame']==name and not r['trail'] and not r['reserved'] and r['snr_peak']>5 and r['rms_normalized']<1.6 and min(np.exp(r['parameters'][2:4]))>.605 and max(np.exp(r['parameters'][2:4]))<3.995];cov=[]
 for r in good:
  p=r['parameters'];c,s=np.cos(p[4]),np.sin(p[4]);rot=np.array([[c,-s],[s,c]]);cov.append(rot@np.diag(np.exp(2*np.array(p[2:4])))@rot.T)
 if not cov:raise RuntimeError('no train '+name)
 cov=np.average(cov,axis=0,weights=[min(r['snr_peak'],30)**2 for r in good]);eig,rot=np.linalg.eigh(cov);pa=[0,0,np.log(np.sqrt(eig[1])),np.log(np.sqrt(eig[0])),np.arctan2(rot[1,1],rot[0,1])];pars[name]=dict(model='pixel-integrated elliptical Gaussian',train_stars=len(good),parameters=pa,coadd_broadening_removed=True)
 results=[]
 for i,row in enumerate(meta['rows']):
  p=pa.copy();p[:2]=(f['expected'][i]-f['origin'][i]).tolist();t=prf(p);z=f['data'][i];col=f['colour'][i];valid=f['valid'][i];planes=[]
  for cfa in range(4):
   mask=(col==cfa)&valid
   if mask.sum()<24 or (mask&ann).sum()<16 or np.sum(t[mask]**2)<1e-9:
    planes.append(dict(flux=0.,error=float('inf'),snr=0.,noise=None,reduced_chi2=None,background=None));continue
   v=z[mask].astype(float);x=X[mask]/12;y=Y[mask]/12;B=np.c_[x*0+1,x,y,x*x,y*y,x*y];tt=t[mask];D=np.c_[tt,B];q=np.linalg.lstsq(D,v,rcond=None)[0];res=v-D@q;sig=max(1.4826*np.median(abs(res[ann[mask]]-np.median(res[ann[mask]]))),.025);ivar=float(np.sum(np.linalg.pinv(D)[0]**2));err=sig*np.sqrt(ivar);planes.append(dict(flux=float(q[0]),error=float(err),snr=float(q[0]/err),noise=float(sig),reduced_chi2=float(np.mean((res/sig)**2)),background=float(q[1])))
  # independent green CFA planes combined statistically; no prior positivity.
  w=np.array([1/planes[j]['error']**2 for j in [1,3]]);fl=sum(w[k]*planes[j]['flux'] for k,j in enumerate([1,3]))/max(w.sum(),1e-30);er=1/np.sqrt(max(w.sum(),1e-30));results.append(dict(index=i,planes=planes,green_flux=float(fl),green_error=float(er),green_snr=float(fl/er)))
 preds[name]=results;print(name,'sigma',np.sqrt(eig),'training',len(good),flush=True)
rows=[]
for i,row in enumerate(meta['rows']):
 by={};
 for group,names in [('A',['DSC06984','DSC06985','DSC06987']),('C',['DSC06991','DSC06993','DSC06996','DSC06999']),('short',['DSC06984','DSC06985','DSC06991','DSC06996','DSC06999']),('all',[r['name'] for r in meta['frames']])]:
  qs=[preds[n][i] for n in names];w=np.array([1/q['green_error']**2 for q in qs]);flux=np.dot(w,[q['green_flux'] for q in qs])/w.sum();err=1/np.sqrt(w.sum());by[group]=dict(flux=float(flux),error=float(err),snr=float(flux/err))
 # Fixed native significance gates: total >=8 and each independent pointing>=4.
 # Same data decision logic for all nulls, existing stars and new candidates. No threshold tuning.
 accept=by['all']['snr']>=8 and min(by['A']['snr'],by['C']['snr'])>=4
 if row['kind']!='psf_reference':accept=accept and row['separation']<=2.5
 rows.append(dict(**row,native=by,native_accept=bool(accept),native_planes={n:preds[n][i]['planes'] for n in preds}))
for kind in ['catalog','rotated_null']:print(kind,sum(r['kind']==kind and r['native_accept'] for r in rows),flush=True)
(O/'S5_native_detection.json').write_text(json.dumps(dict(models=pars,rows=rows),indent=2));print('COMPLETE',flush=True)
