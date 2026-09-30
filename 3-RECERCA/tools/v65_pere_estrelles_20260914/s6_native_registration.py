from pathlib import Path
import numpy as np,json
from scipy.optimize import least_squares
from scipy.ndimage import gaussian_filter
from s4_native_psf import prf,design,X,Y,ann
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';meta=json.loads((O/'S3_native_manifest.json').read_text());rows=[]
def fit(data,col,valid,xy,origin):
 mask,B=design(col,valid);z=data[mask].astype(float);bg=np.linalg.lstsq(B[ann[mask]],z[ann[mask]],rcond=None)[0];noise=max(1.4826*np.median(abs((z-B@bg)[ann[mask]])),.025);dx,dy=np.array(xy)-origin
 def calc(p,ret=False):
  t=prf(p)[mask];D=np.c_[t,B];q=np.linalg.lstsq(D,z,rcond=None)[0];res=(D@q-z)/noise
  return (q,res) if ret else res
 ss=gaussian_filter(np.where(mask,data,0),1)/np.maximum(gaussian_filter(mask.astype(float),1),1e-8);sel=(abs(X-dx)<6)&(abs(Y-dy)<6);sy,sx=np.unravel_index(np.argmax(np.where(sel,ss,-np.inf)),ss.shape);px,py=sx-12,sy-12
 init=[px,py,np.log(1.3),np.log(2),0];lo=[dx-7,dy-7,np.log(.55),np.log(.55),-np.pi];hi=[dx+7,dy+7,np.log(7),np.log(7),np.pi]
 sol=least_squares(calc,init,bounds=(lo,hi),loss='soft_l1',f_scale=2,max_nfev=100);q,res=calc(sol.x,True);p=sol.x
 return dict(parameters=p.tolist(),x=float(origin[0]+p[0]),y=float(origin[1]+p[1]),predicted=list(map(float,xy)),flux=float(q[0]),noise=float(noise),rms_normalized=float(np.sqrt(np.mean(res**2))),snr_peak=float(q[0]*prf(p).max()/noise))
for fr in meta['frames']:
 name=fr['name'];f=np.load(O/f'S3_{name}.npz')
 for i,r in enumerate(meta['rows']):
  if r['kind']!='psf_reference' or r['V']>8:continue
  q=fit(f['data'][i],f['colour'][i],f['valid'][i],f['expected'][i],f['origin'][i]);rows.append(dict(frame=name,index=i,det=r['det'],reserved=r['reserved'],V=r['V'],**q))
 print(name,'native recovered',len(rows),flush=True)
 (O/'S6_native_registration_progress.json').write_text(json.dumps(rows,indent=2))
# Fit residual similarity relative to initial per-frame prediction; heldout objects do not enter fit.
trans={}
for fr in meta['frames']:
 name=fr['name'];sel=[r for r in rows if r['frame']==name and not r['reserved'] and r['snr_peak']>5 and r['rms_normalized']<1.8 and max(np.exp(r['parameters'][2:4]))<6.9];positions=np.array([r['predicted'] for r in sel]);delta=np.array([[r['x'],r['y']] for r in sel])-positions;cen=np.array([3984,2660]);uv=(positions-cen)/4000;D=np.zeros((2*len(sel),4));D[::2]=np.c_[np.ones(len(sel)),np.zeros(len(sel)),uv[:,0],-uv[:,1]];D[1::2]=np.c_[np.zeros(len(sel)),np.ones(len(sel)),uv[:,1],uv[:,0]];w=np.repeat(np.minimum([r['snr_peak'] for r in sel],30),2)
 sol=least_squares(lambda p:(D@p-delta.ravel())*np.sqrt(w/w.max()),np.zeros(4),loss='soft_l1',f_scale=.3);p=sol.x
 def predict(xy):
  u,v=(np.array(xy)-cen)/4000;return np.array(xy)+[p[0]+p[2]*u-p[3]*v,p[1]+p[2]*v+p[3]*u]
 held=[r for r in rows if r['frame']==name and r['reserved'] and r['snr_peak']>5];res=[float(np.linalg.norm(predict(r['predicted'])-[r['x'],r['y']])) for r in held];trans[name]=dict(parameters=p.tolist(),centre=cen.tolist(),scale_unit=4000,train=len(sel),held_out=res,held_out_median=float(np.median(res)) if res else None);print(name,trans[name],flush=True)
(O/'S6_native_registration.json').write_text(json.dumps(dict(measurements=rows,transforms=trans,claim='Only registers new star measurements between native exposures. Pere project coordinates remain unchanged.'),indent=2));print('COMPLETE',flush=True)
