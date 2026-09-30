from pathlib import Path
import numpy as np,json
from scipy.optimize import least_squares
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';meta=json.loads((O/'S3_native_manifest.json').read_text());Y,X=np.mgrid[-12:13,-12:13];XY=np.stack([X,Y],-1);ann=np.hypot(X,Y)>8
# Pixel integration by three-point Gauss-Legendre quadrature on each pixel, compared later to finer quadrature.
nodes=np.sqrt(3/5)*np.array([-.5,0,.5]);weights=np.array([5,8,5])/18

def prf(p,trail=False):
 dx,dy,sx,sy,th=p;c,s=np.cos(th),np.sin(th);out=np.zeros((25,25));sx=np.exp(sx);sy=np.exp(sy)
 for u,wu in zip(nodes,weights):
  for v,wv in zip(nodes,weights):
   a=(X+u-dx)*c+(Y+v-dy)*s;b=-(X+u-dx)*s+(Y+v-dy)*c
   if trail:
    from scipy.special import erf
    length=sy;z=(erf((a+length/2)/(np.sqrt(2)*sx))-erf((a-length/2)/(np.sqrt(2)*sx)))/(2*length)*np.exp(-.5*(b/sx)**2)/(np.sqrt(2*np.pi)*sx)
   else:z=np.exp(-.5*((a/sx)**2+(b/sy)**2))/(2*np.pi*sx*sy)
   out+=wu*wv*z
 return out

def design(col,valid):
 mask=valid&((col==1)|(col==3));g=col[mask];x=X[mask]/12;y=Y[mask]/12;B=np.c_[(g==1),(g==3),x,y,x*x,y*y,x*y].astype(float);return mask,B

def fit(data,col,valid,xy,origin,trail=False):
 mask,B=design(col,valid);z=data[mask].astype(float);bg=np.linalg.lstsq(B[ann[mask]],z[ann[mask]],rcond=None)[0];noise=max(1.4826*np.median(abs((z-B@bg)[ann[mask]])),.025);dx,dy=np.array(xy)-origin
 def pred(p,ret=False):
  f=prf(p,trail)[mask];D=np.c_[f,B];q=np.linalg.lstsq(D,z,rcond=None)[0];res=(D@q-z)/noise
  if ret:return q,res
  return res
 init=[dx,dy,np.log(1.3),np.log(3 if trail else 1.3),0];lo=[dx-2,dy-2,np.log(.6),np.log(.1 if trail else .6),-np.pi];hi=[dx+2,dy+2,np.log(4),np.log(9 if trail else 4),np.pi]
 sol=least_squares(pred,init,bounds=(lo,hi),loss='soft_l1',f_scale=2,max_nfev=65);q,res=pred(sol.x,True);rss=float(np.mean(res*res));return dict(parameters=sol.x.tolist(),flux=float(q[0]),noise=float(noise),rms_normalized=float(np.sqrt(rss)),snr_peak=float(q[0]*prf(sol.x,trail).max()/noise),trail=trail)
if __name__=='__main__':
 rows=[]
 for fr in meta['frames']:
  name=fr['name'];f=np.load(O/f'S3_{name}.npz')
  for i,r in enumerate(meta['rows']):
   if r['kind']!='psf_reference' or r['V']>8:continue
   for trail in [False,True]:
    q=fit(f['data'][i],f['colour'][i],f['valid'][i],f['expected'][i],f['origin'][i],trail);rows.append(dict(frame=name,exposure=fr['exposure'],index=i,det=r['det'],reserved=r['reserved'],V=r['V'],**q))
  print(name,'fitted',len(rows),flush=True)
  (O/'S4_native_psf_progress.json').write_text(json.dumps(rows,indent=2))
 (O/'S4_native_psf.json').write_text(json.dumps(rows,indent=2));print('COMPLETE',flush=True)
