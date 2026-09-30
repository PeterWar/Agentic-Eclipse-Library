from pathlib import Path
import numpy as np,json
from s4_native_psf import prf,X,Y
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';meta=json.loads((O/'S16_extra_manifest.json').read_text());spec=json.loads((O/'S14_multiband_detection.json').read_text())['Sony']['spectral_coefficients'];ann=np.hypot(X,Y)>8;preds={}
for fr in meta['frames']:
 name=fr['name'];f=np.load(O/f'S16_{name}.npz');pa=meta['models'][name];results=[]
 for i,row in enumerate(meta['rows']):
  p=pa.copy();p[:2]=(f['expected'][i]+row['long_frame_centroid_offset']-f['origin'][i]).tolist();t=prf(p);z=f['data'][i];col=f['colour'][i];valid=f['valid'][i];planes=[]
  for cfa in range(4):
   mask=(col==cfa)&valid
   if mask.sum()<24 or (mask&ann).sum()<16 or np.sum(t[mask]**2)<1e-9:planes.append(dict(flux=0.,error=float('inf'),snr=0.,noise=None,reduced_chi2=None,background=None));continue
   v=z[mask].astype(float);x=X[mask]/12;y=Y[mask]/12;B=np.c_[x*0+1,x,y,x*x,y*y,x*y];tt=t[mask];D=np.c_[tt,B];q=np.linalg.lstsq(D,v,rcond=None)[0];res=v-D@q;sig=max(1.4826*np.median(abs(res[ann[mask]]-np.median(res[ann[mask]]))),.025);ivar=float(np.sum(np.linalg.pinv(D)[0]**2));err=sig*np.sqrt(ivar);planes.append(dict(flux=float(q[0]),error=float(err),snr=float(q[0]/err),noise=float(sig),reduced_chi2=float(np.mean((res/sig)**2)),background=float(q[1])))
  results.append(planes)
 preds[name]=results;print(name,flush=True)
rows=[]
for i,row in enumerate(meta['rows']):
 master='DSC06987' if row['split']=='A' else 'DSC06993';bv=np.clip(row['BV'],0,1.8) if np.isfinite(row['BV']) else .65;q=np.array([np.exp(spec['R'][0]+spec['R'][1]*bv),1,np.exp(spec['B'][0]+spec['B'][1]*bv),1]);by={};green={}
 for group,names in [('long',[master]),('reserved',[n for n in preds if n!=master]),('all',list(preds))]:
  pp=np.array([[[v['flux'],v['error']] for v in preds[n][i]] for n in names]);w=1/pp[...,1]**2
  for out,qq in [(by,q),(green,np.array([0,1,0,1]))]:
   den=np.sum(w*qq*qq);f=np.sum(w*qq*pp[...,0])/max(den,1e-30);e=1/np.sqrt(max(den,1e-30));out[group]=dict(flux=float(f),error=float(e),snr=float(f/e))
 accept=any(d['all']['snr']>=8 and min(d['long']['snr'],d['reserved']['snr'])>=4 for d in [by,green]);rows.append(dict(**row,native=green,multiband=by,accepted=bool(accept),native_planes={n:preds[n][i] for n in preds}))
for k in ['catalog','rotated_null']:print(k,sum(r['kind']==k and r['accepted'] for r in rows),flush=True)
(O/'S17_extra_detection.json').write_text(json.dumps(dict(rows=rows,thresholds=dict(each_independent_min=4,total_min=8),spectral_coefficients=spec),indent=2));print('COMPLETE')
