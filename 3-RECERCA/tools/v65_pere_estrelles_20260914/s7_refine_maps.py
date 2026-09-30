from pathlib import Path
import numpy as np,json,pandas as pd
from scipy.optimize import least_squares
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';meta=json.loads((O/'S3_native_manifest.json').read_text());s6=json.loads((O/'S6_native_registration.json').read_text());s1=json.loads((O/'S1_psf_stacks.json').read_text());cent=np.array([3984,2660]);scale=4000
def design(xy):
 xy=(np.atleast_2d(xy)-cent)/scale;x,y=xy.T;return np.c_[x*0+1,x,y,x*x,x*y,y*y]
rows=[]
for name in sorted(set(r['det'] for r in s1)):
 a=next(r for r in s1 if r['det']==name and r['group']=='A');c=next(r for r in s1 if r['det']==name and r['group']=='C')
 if min(a['snr_peak'],c['snr_peak'])<5:continue
 rows.append(dict(det=name,A=[a['x'],a['y']],C=[c['x'],c['y']],reserved=a['reserved'],snr=min(a['snr_peak'],c['snr_peak'])))
train=[r for r in rows if not r['reserved']];D=design([r['C'] for r in train]);tar=np.array([r['A'] for r in train]);coef=np.linalg.lstsq(D,tar,rcond=None)[0];held=[r for r in rows if r['reserved']];res=np.linalg.norm(design([r['C'] for r in held])@coef-[r['A'] for r in held],axis=1);maps=dict(model='Quadratic lens mapping between Sony C and A; measured individual star centroids, frozen one-third holdout',centre=cent.tolist(),scale=scale,coefficients_C_to_A=coef.tolist(),train=len(train),held_out=[dict(det=r['det'],error=float(e)) for r,e in zip(held,res)],held_out_median=float(np.median(res)),held_out_max=float(res.max()));print('interpointing',maps,flush=True)
trans={}
for fr in meta['frames']:
 name=fr['name'];g='A' if name in ['DSC06984','DSC06985','DSC06987'] else 'C';items=[]
 for r in s6['measurements']:
  if r['frame']!=name:continue
  ref=next(s for s in s1 if s['det']==r['det'] and s['group']==g);pred=np.array([ref['x'],ref['y']])+fr['offset'];items.append(dict(**r,stack_prediction=pred.tolist()))
 sel=[r for r in items if not r['reserved'] and r['snr_peak']>5 and r['rms_normalized']<1.8 and max(np.exp(r['parameters'][2:4]))<6.9];pos=np.array([r['stack_prediction'] for r in sel]);delta=np.array([[r['x'],r['y']] for r in sel])-pos
 if len(sel)<3:
  # Underdetermined rotation/scale: estimate only translation from available training stars; holdout remains the judge.
  p=np.r_[np.average(delta,axis=0,weights=[r['snr_peak']**2 for r in sel]),0.,0.]
 else:
  uv=(pos-cent)/scale;D=np.zeros((2*len(sel),4));D[::2]=np.c_[np.ones(len(sel)),np.zeros(len(sel)),uv[:,0],-uv[:,1]];D[1::2]=np.c_[np.zeros(len(sel)),np.ones(len(sel)),uv[:,1],uv[:,0]];w=np.repeat(np.minimum([r['snr_peak'] for r in sel],30),2);sol=least_squares(lambda p:(D@p-delta.ravel())*np.sqrt(w/w.max()),np.zeros(4),loss='soft_l1',f_scale=.3);p=sol.x
 def pred(xy):
  u,v=(np.array(xy)-cent)/scale;return np.array(xy)+[p[0]+p[2]*u-p[3]*v,p[1]+p[2]*v+p[3]*u]
 held=[r for r in items if r['reserved'] and r['snr_peak']>5];err=[np.linalg.norm(pred(r['stack_prediction'])-[r['x'],r['y']]) for r in held];trans[name]=dict(parameters=p.tolist(),centre=cent.tolist(),scale_unit=scale,train=len(sel),held_out=[dict(det=r['det'],error=float(e)) for r,e in zip(held,err)],held_out_median=float(np.median(err)),held_out_max=float(max(err)));print(name,trans[name],flush=True)
(O/'S7_refined_maps.json').write_text(json.dumps(dict(interpointing=maps,native_transforms=trans,previous_diagnostic='S6 fits relative to legacy A/C map confounded optical distortion with mount motion. The direct native stack centroids separate those effects.'),indent=2));print('COMPLETE')
