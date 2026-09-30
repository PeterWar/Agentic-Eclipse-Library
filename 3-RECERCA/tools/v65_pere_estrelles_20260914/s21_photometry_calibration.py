from pathlib import Path
import json,numpy as np
O=Path.cwd()/'output/v65_pere_estrelles_20260914';d=json.loads((O/'S19_native_measure.json').read_text());out={}
for n in sorted({r['frame'] for r in d['references']}):
 rows=[]
 for r in d['references']:
  if r['frame']!=n or r['V']>=8:continue
  q=r['planes'];w=np.array([1/q[i]['error']**2 for i in [1,3]]);wa=np.array([1/q[i]['aperture_error']**2 for i in [1,3]]);f=np.dot(w,[q[i]['flux'] for i in [1,3]])/w.sum();fa=np.dot(wa,[q[i]['aperture'] for i in [1,3]])/wa.sum();e=1/np.sqrt(wa.sum());rows.append((r['reserved'],f,fa,e))
 train=np.array([r[1:] for r in rows if not r[0]]);held=np.array([r[1:] for r in rows if r[0]]);w=1/train[:,2]**2;cal=np.sum(w*train[:,0]*train[:,1])/np.sum(w*train[:,0]**2);er=1/np.sqrt(np.sum(w*train[:,0]**2));res=(held[:,1]-cal*held[:,0])/np.sqrt(held[:,2]**2+(er*held[:,0])**2);out[n]=dict(calibration=float(cal),error=float(er),train=len(train),held_n=len(held),held_residual_sigma=res.tolist(),held_rms_sigma=float(np.sqrt(np.mean(res**2))))
(O/'S21_photometry_calibration.json').write_text(json.dumps(out,indent=2));print('COMPLETE')
