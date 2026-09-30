from pathlib import Path
import numpy as np,json
from scipy.optimize import least_squares,root
from s4_native_psf import prf,X,Y,ann
from s18_transport import final
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';joint=json.loads((O/'S15_joint_catalog.json').read_text());extra=json.loads((O/'S17_extra_detection.json').read_text());spec=json.loads((O/'S14_multiband_detection.json').read_text());mp=json.loads((O/'S7_refined_maps.json').read_text());reg=mp['native_transforms'];models={'Sony':json.loads((O/'S10_native_detection.json').read_text())['models'],'Vixen':json.loads((O/'S13_vixen_detection.json').read_text())['models']};meta={k:json.loads((O/(v+'.json')).read_text()) for k,v in [('Sony','S9_native_manifest'),('Vixen','S11_vixen_manifest'),('extra','S16_extra_manifest')]};sets={k:{r['TYC']:i for i,r in enumerate(v['rows']) if r['kind']=='catalog'} for k,v in meta.items()};cat={r['TYC']:r for r in joint['rows'] if r['kind']=='catalog' and r['accepted']};
for r in extra['rows']:
 if r['kind']!='catalog' or not r['accepted']:continue
 if r['TYC'] not in cat:cat[r['TYC']]=dict(TYC=r['TYC'],HIP=r['HIP'],V=r['V'],BV=r['BV'],x=r['x_final'],y=r['y_final'],accepted=True,Sony_source=None,Vixen_source=None)
 cat[r['TYC']]['Sony_extra']=r
fs={k:{fr['name']:np.load(O/f'{pre}_{fr["name"]}.npz') for fr in m['frames']} for k,m,pre in [('Sony',meta['Sony'],'S9'),('Vixen',meta['Vixen'],'S11'),('extra',meta['extra'],'S16')]}
def delta_native(xy,name):
 r=reg[name];u,v=(np.array(xy)-r['centre'])/r['scale_unit'];a,b,k,t=r['parameters'];return np.array([a+k*u-t*v,b+k*v+t*u])
def unframe(xy,name):
 # Exact inverse of the measured native reference-star mapping, no HDR fit.
 r=reg[name];a,b,k,t=r['parameters'];s=r['scale_unit'];M=np.array([[1+k/s,-t/s],[t/s,1+k/s]]);b0=np.array([a,b])-(M-np.eye(2))@r['centre'];p=np.linalg.solve(M,np.array(xy)-b0);fr=next(q for q in meta['Sony']['frames'] if q['name']==name);p-=fr['offset']
 if name in ['DSC06984','DSC06985','DSC06987']:
  co=np.array(mp['interpointing']['coefficients_C_to_A']);cent=np.array(mp['interpointing']['centre']);scale=mp['interpointing']['scale']
  def fun(q):
   u,v=(q-cent)/scale;return np.array([1,u,v,u*u,u*v,v*v])@co-p
  p=root(fun,p).x
 return p
def c_final(c):
 fr=next(q for q in meta['Sony']['frames'] if q['name']=='DSC06993');p=np.array(c)+fr['offset'];return final(p+delta_native(p,'DSC06993'),'sony','DSC06993')
def measure(z,col,valid,p0,refine=True):
 mask=valid&((col==1)|(col==3));x=X[mask]/12;y=Y[mask]/12;B=np.c_[(col[mask]==1),(col[mask]==3),x,y,x*x,y*y,x*y].astype(float);v=z[mask].astype(float)
 if mask.sum()<32 or (mask&ann).sum()<20:return None
 def calc(delta,ret=False):
  p=p0.copy();p[:2]=(np.array(p0[:2])+delta).tolist();t=prf(p);D=np.c_[t[mask],B];q=np.linalg.lstsq(D,v,rcond=None)[0];res=v-D@q;noise=max(1.4826*np.median(abs(res[ann[mask]]-np.median(res[ann[mask]]))),.025)
  if ret:return p,t,q,noise,res
  return res
 p,t,q,noise,res=calc([0,0],True);D=np.c_[t[mask],B];er=noise*np.linalg.norm(np.linalg.pinv(D)[0]);snr=q[0]/er
 if refine and snr>=5:
  fit=least_squares(lambda d:calc(d)/noise,np.zeros(2),bounds=(-2.5,2.5),loss='soft_l1',f_scale=2,max_nfev=30);p,t,q,noise,res=calc(fit.x,True)
 planes=[]
 for cfa in range(4):
  mask=valid&(col==cfa);x=X[mask]/12;y=Y[mask]/12;B=np.c_[x*0+1,x,y,x*x,y*y,x*y];v=z[mask].astype(float)
  if mask.sum()<24 or (mask&ann).sum()<16:planes.append(dict(flux=0,error=float('inf'),aperture=0,aperture_error=float('inf')));continue
  D=np.c_[t[mask],B];q=np.linalg.lstsq(D,v,rcond=None)[0];res=v-D@q;sig=max(1.4826*np.median(abs(res[ann[mask]]-np.median(res[ann[mask]]))),.025);err=sig*np.linalg.norm(np.linalg.pinv(D)[0]);rr=np.hypot(X-p[0],Y-p[1]);bgsel=rr[mask]>8;ap=rr[mask]<=8
  if bgsel.sum()<16:apflux=0;aperr=float('inf')
  else:
   bg=np.linalg.lstsq(B[bgsel],v[bgsel],rcond=None)[0];norm=t[mask][ap].sum();apflux=np.sum((v-B@bg)[ap])/max(norm,1e-10);h=np.sum(B[ap],axis=0)@np.linalg.pinv(B[bgsel]);aperr=sig*np.sqrt(ap.sum()+h@h)/max(norm,1e-10)
  planes.append(dict(flux=float(q[0]),error=float(err),aperture=float(apflux),aperture_error=float(aperr),chi2=float(np.mean((res/sig)**2))))
 return dict(parameters=p,green_snr=float(snr),planes=planes,centroid_refined=bool(refine and snr>=5))
if __name__=='__main__':
 results=[];references=[]
 for source in ['Sony','extra','Vixen']:
  tag='Sony' if source=='extra' else source;m=meta[source];wanted=[(i,r) for i,r in enumerate(m['rows']) if r['kind']=='psf_reference' or r['kind']=='catalog' and r['TYC'] in cat and (source!='extra' or cat[r['TYC']].get('Sony_extra'))]
  for fr in m['frames']:
   name=fr['name'];f=fs[source][name];pa=models[tag][name]['parameters'];n=0
   for i,r in wanted:
    p=np.array(f['expected'][i],float);p+=delta_native(p,name) if source=='Sony' else (np.array(r.get('long_frame_centroid_offset',[0,0])) if source=='extra' else models[tag][name]['offset']);p0=list(pa);p0[:2]=(p-f['origin'][i]).tolist();q=measure(f['data'][i],f['colour'][i],f['valid'][i],p0)
    if q is None:continue
    xy=np.array(q['parameters'][:2])+f['origin'][i];out=dict(source=source,frame=name,index=i,TYC=r.get('TYC'),det=r.get('det'),kind=r['kind'],reserved=r.get('reserved'),V=r['V'],xy=xy.tolist(),**q)
    if tag=='Sony':out['C_reference']=unframe(xy,name).tolist();out['final_xy']=c_final(out['C_reference']).tolist()
    (references if r['kind']=='psf_reference' else results).append(out);n+=1
   print(source,name,n,flush=True)
   (O/'S19_native_measure_progress.json').write_text(json.dumps(dict(measurements=results,references=references),indent=2))
 (O/'S19_native_measure.json').write_text(json.dumps(dict(measurements=results,references=references,catalog=list(cat.values()),transport='Measured native centroids -> Sony C reference -> existing V42 projection, no new HDR plate or image transform.'),indent=2));print('COMPLETE')
