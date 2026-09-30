"""Independent paired injection and null controls for nominal-mass RHEF."""
from pathlib import Path
import json,types,numpy as np,cv2
from scipy.ndimage import map_coordinates
R=Path(__file__).resolve().parents[3];T=Path(__file__).parent;O=R/'4-RESULTATS/v112_20260928'
def module(path,name,trace=False):
 s=path.read_text()
 if trace:s=s.replace('return result','trace=np.zeros(a.shape,np.float32); trace.ravel()[idx]=affected; return result,trace')
 mod=types.ModuleType(name);exec(compile(s,str(path),'exec'),mod.__dict__);return mod
old=module(R/'3-RECERCA/tools/v98_20260925/rhef_local_sim.py','legacy');new=module(T/'rhef_mass.py','mass',True)
cv2.setNumThreads(2);N=1536;cx=cy=768.;yy,xx=np.mgrid[:N,:N].astype(np.float32);rr=np.hypot(xx-cx,yy-cy);tt=np.arctan2(yy-cy,xx-cx)
m=(rr>=100)&(rr<=730)&(yy>=260);full=m&(rr>=150)&(rr<=480)
def run(mod,a,S):return mod.rhef_local_sim(a,m,rr,tt,S,S/4,cx,cy,log=lambda *a:None,dr=.5,nt=16384,simetric=True,detrend=False,nmin=200)
def ds(a,b,sel):
 d=(a[sel]-b[sel]).astype(float);return dict(n=len(d),finite=int(np.isfinite(d).sum()),changed=int(np.count_nonzero(d)),maxabs=float(np.nanmax(abs(d))),rms=float(np.sqrt(np.nanmean(d*d))))
rep=dict(scope='Synthetic derived linear inputs; complete-domain transfer gate only; partial attenuation reported separately',canvas=[N,N],full_domain='150<=r<=480',mode='S30/60; nt16384; dr0.5; symmetrical; no detrend; legacy nmin200',results={})
for S in (30,60):
 d={};qo=run(old,np.ones((N,N),np.float32),S);qn,aff=run(new,np.ones((N,N),np.float32),S);bo=m&~np.isfinite(qo);bn=m&~np.isfinite(qn)
 d['constant']=dict(maxabs_half=float(np.nanmax(abs(qn[m]-.5))),old_nan=int(bo.sum()),new_nan=int(bn.sum()),newly_undefined=int((bn&~bo).sum()),remaining_nan_partial=int((bn&(aff>0)).sum()),full_identity=ds(qo,qn,full))
 a=np.exp((.35*(xx-cx)+.55*(yy-cy))/N).astype(np.float32);go=run(old,a,S);gn,aff=run(new,a,S);d['gradient']={};radii=np.arange(480.,725.01,.5)
 for theta in (220.,250.,290.,320.):
  th=np.deg2rad(theta);coords=[cy+radii*np.sin(th),cx+radii*np.cos(th)];ok=map_coordinates(m.astype(np.float32),coords,order=1,mode='constant',cval=0,prefilter=False)>=1-1e-6;ix=np.flatnonzero(ok);ii=max(np.split(ix,np.where(np.diff(ix)>1)[0]+1),key=len);pa=map_coordinates(aff,coords,order=1,mode='constant',cval=0,prefilter=False)[ii];entry=np.flatnonzero((pa>1e-7)&np.r_[False,pa[:-1]<=1e-7]);z={}
  for name,img in [('legacy',go),('mass',gn)]:
   v=map_coordinates(img,coords,order=1,mode='constant',cval=np.nan,prefilter=False)[ii];z[name]=dict(max_halfpx_step=float(np.nanmax(abs(np.diff(v)))),entry_steps=[float(v[j]-v[j-1]) for j in entry if np.isfinite(v[j]) and np.isfinite(v[j-1])])
  d['gradient'][str(theta)]=z
 rng=np.random.default_rng(112);base=np.exp(-.75*rr/730+.16*np.cos(3*tt)+.06*np.sin(7*tt)+.03*np.cos(2*np.pi*(xx+yy)/450)+.002*rng.standard_normal((N,N))).astype(np.float32);d['injections']={}
 for lam in (96,160,256):
  wave=np.cos(2*np.pi*(.6*(xx-cx)+.8*(yy-cy))/lam+.37).astype(np.float32);eps=.005;op=run(old,base*(1+eps*wave),S);np_,ap=run(new,base*(1+eps*wave),S);om=run(old,base*(1-eps*wave),S);nm,am=run(new,base*(1-eps*wave),S);ro=(op-om)/(2*eps);rn=(np_-nm)/(2*eps)
  def project(a,sel):
   w=wave[sel].astype(float);w-=w.mean();return float(np.dot(a[sel],w)/np.dot(w,w))
  partial=m&((ap>0)|(am>0))&np.isfinite(ro)&np.isfinite(rn);tr=project(rn,full)/project(ro,full)
  d['injections'][str(lam)]=dict(full_transfer=tr,full_identity=ds(ro,rn,full),partial_transfer=project(rn,partial)/project(ro,partial),partial_pixels=int(partial.sum()),pass_full_transfer=.9<=tr<=1.1)
 rep['results'][str(S)]=d;print('Completed',S,flush=True)
rep['status']='PASS_FULL_SUPPORT_ONLY' if all(v['pass_full_transfer'] for d in rep['results'].values() for v in d['injections'].values()) else 'FAIL'
(O/'MASS_SYNTHETIC.json').write_text(json.dumps(rep,indent=2)+'\n');print(rep['status'])
