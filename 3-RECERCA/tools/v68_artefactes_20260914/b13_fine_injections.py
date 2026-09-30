from pathlib import Path
import ast,numpy as np,json,time
from scipy.sparse.linalg import LinearOperator,cg
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';tree=ast.parse((R/'research/tools/v68_artefactes_20260914/b9_fine_detector.py').read_text());body=[]
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(q,ast.Name) and q.id=='rep' for q in node.targets):break
 body.append(node)
ns={'__name__':'frozen_operator'};exec(compile(ast.Module(body=body,type_ignores=[]),'frozen','exec'),ns)
W=ns['W'];OW=ns['OW'];r=ns['r'];physical=ns['physical'];filt=ns['filt'];pull=ns['pull'];push=ns['push'];N=ns['N'];count=len(W);dd=W.sum(0);oden=OW.sum(0);ridge=.1*np.median(dd[(r<300)&(dd>0)]);gain=np.load(A/'B9_fine_detector.npz')['gain'];from scipy.fft import rfft2,irfft2

def remove(values):
 base=sum(W[i]*values[i] for i in range(count))/np.maximum(dd,1e-30);rhs=filt(sum(push(W[i]*(values[i]-base),i) for i in range(count)))
 def op(v):
  D=filt(v.reshape(N,N));p=[pull(D,i) for i in range(count)];av=sum(W[i]*p[i] for i in range(count))/np.maximum(dd,1e-30);return (filt(sum(push(W[i]*(p[i]-av),i) for i in range(count)))+ridge*v.reshape(N,N)).ravel()
 if np.linalg.norm(rhs)<1e-12:D=np.zeros((N,N),np.float32)
 else:
  mat=LinearOperator((N*N,N*N),matvec=op,dtype=np.float32);sol,info=cg(mat,rhs.ravel(),rtol=3e-5,maxiter=80);assert info==0;D=irfft2(rfft2(filt(sol.reshape(N,N)))*gain,s=(N,N))
 raw=sum(OW[i]*values[i] for i in range(count))/np.maximum(oden,1e-30);corr=sum(OW[i]*pull(D,i) for i in range(count))/np.maximum(oden,1e-30);return raw,raw-corr
rng=np.random.default_rng(680914);y,x=np.mgrid[:N,:N];result=[]
for wave in [4.5,6,9,12,24,48]:
 angle=float(rng.uniform(0,np.pi));phase=float(rng.uniform(0,2*np.pi));s=np.cos((x*np.cos(angle)+y*np.sin(angle))*2*np.pi/wave+phase).astype('float32');s*=np.exp(-((x-699.6)**2+(y-699.6)**2)/(2*240**2)).astype('float32')
 for kind in ['scene','detector']:
  vals=[s if kind=='scene' else pull(s,i) for i in range(count)];before,after=remove(vals);mask=physical&(r<410);transfer=float(np.sum(before[mask]*after[mask])/np.sum(before[mask]**2));rmsratio=float(np.std(after[mask])/np.std(before[mask]));row=dict(wavelength=wave,angle=angle,kind=kind,transfer=transfer,rms_ratio=rmsratio,pass_gate=(.9<=transfer<=1.1) if kind=='scene' else rmsratio<=1.1);result.append(row);print(row,flush=True)
rep=dict(rows=result,all_pass=all(q['pass_gate'] for q in result),limits=['Differential tests of frozen nuisance weights and repeatability gains; do not retrain the error model.','Common scene invariance is algebraic in the free-scene model. Detector-only controls and independent Sony comparison provide additional evidence.','Photographic transport remains empirical, not a new raw-to-CameraRaw precision claim.']);(O/'B13_injections.json').write_text(json.dumps(rep,indent=2)+'\n')
