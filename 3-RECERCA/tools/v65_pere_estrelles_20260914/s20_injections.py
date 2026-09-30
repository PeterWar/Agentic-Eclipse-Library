from pathlib import Path
import json,numpy as np
from scipy.special import erf
from s4_native_psf import prf,X,Y,ann
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';out=[];quad=[]
def finer(p,trail=False):
 nodes,weights=np.polynomial.legendre.leggauss(7);nodes/=2;weights/=2;dx,dy,sx,sy,th=p;sx=np.exp(sx);sy=np.exp(sy);c,s=np.cos(th),np.sin(th);z=np.zeros((25,25))
 for u,wu in zip(nodes,weights):
  for v,wv in zip(nodes,weights):
   a=(X+u-dx)*c+(Y+v-dy)*s;b=-(X+u-dx)*s+(Y+v-dy)*c
   if trail:g=(erf((a+sy/2)/(np.sqrt(2)*sx))-erf((a-sy/2)/(np.sqrt(2)*sx)))/(2*sy)*np.exp(-.5*(b/sx)**2)/(np.sqrt(2*np.pi)*sx)
   else:g=np.exp(-.5*((a/sx)**2+(b/sy)**2))/(2*np.pi*sx*sy)
   z+=wu*wv*g
 return z
def fit(z,col,valid,t):
 mask=valid&((col==1)|(col==3));x=X[mask]/12;y=Y[mask]/12;B=np.c_[(col[mask]==1),(col[mask]==3),x,y,x*x,y*y,x*y].astype(float);D=np.c_[t[mask],B];v=z[mask];pinv=np.linalg.pinv(D);q=pinv@v;res=v-D@q;sig=max(1.4826*np.median(abs(res[ann[mask]]-np.median(res[ann[mask]]))),.025);er=sig*np.linalg.norm(pinv[0]);return q[0],er
for tag,pre,manifest,model_file,psf_file,names in [('Sony','S9','S9_native_manifest','S10_native_detection','S4_native_psf',['DSC06985','DSC06987','DSC06993']),('Vixen','S11','S11_vixen_manifest','S13_vixen_detection','S12_vixen_psf',['572A2978','572A2982'])]:
 meta=json.loads((O/(manifest+'.json')).read_text());models=json.loads((O/(model_file+'.json')).read_text())['models'];psfs=json.loads((O/(psf_file+'.json')).read_text());ids=[i for i,r in enumerate(meta['rows']) if r['kind']=='rotated_null'][::17][:12]
 for name in names:
  f=np.load(O/f'{pre}_{name}.npz');p=models[name]['parameters'].copy();tr=[r for r in psfs if r['frame']==name and r['trail'] and not r['reserved'] and r['snr_peak']>5];tp=np.median([r['parameters'][2:4] for r in tr],0) if tr else [np.log(1.2),np.log(2.)]
  for j,i in enumerate(ids):
   if f['valid'][i].sum()<350:continue
   p[:2]=[(j*.37)%1-.5,(j*.61)%1-.5];t=prf(p);truth=finer(p);quad.append(float(np.max(abs(t-truth))));z=f['data'][i].astype(float);col=f['colour'][i];valid=f['valid'][i];base,er=fit(z,col,valid,t)
   for family in ['same_gaussian','line_mismatch']:
    pp=p.copy();pp[2:4]=tp;tt=truth if family=='same_gaussian' else finer(pp,True)
    for snr in [10,30,100]:
     flux=snr*er;est,error=fit(z+tt*flux,col,valid,t);out.append(dict(tag=tag,frame=name,index=i,family=family,snr=snr,conditional_recovery=float((est-base)/flux),unsubtracted_recovery=float(est/flux),baseline_significance=float(base/er)))
  print(tag,name,flush=True)
summary={}
for family in ['same_gaussian','line_mismatch']:
 r=[v for v in out if v['family']==family];q=np.array([v['conditional_recovery'] for v in r]);summary[family]=dict(n=len(r),conditional_median=float(np.median(q)),conditional_range=[float(q.min()),float(q.max())],within10pct=int(np.sum(abs(q-1)<=.1)))
rep=dict(quadrature_max=float(max(quad)),summary=summary,trials=out,scope='Conditional linear transport/integration check on real CFA backgrounds. Not an end-to-end discovery proof. Line mismatch is a deliberately separate robustness test, not reclassified as a Gaussian pass.');(O/'S20_injections.json').write_text(json.dumps(rep,indent=2));print({k:v for k,v in rep.items() if k!='trials'},flush=True)
