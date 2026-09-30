"""Repeatability-qualified red detector, complementing V55 green correction.
R1 attempts to add more red mix fail at the limb; R2/R3 show uncertain colour
increment. Distinct causal claim: remove only the already-present red detector
component supported by dither and repeated in disjoint exposure/time halves.
The previous green method and Fourier bins are reused without parameter search.
"""
from common import *
from scipy.fft import rfft2,irfft2
from scipy.sparse.linalg import LinearOperator,cg
import ast,sys,time
claim();path=ROOT/'research/tools/earthshine_max_detail_20260913/b3_fpn_full.py';tree=ast.parse(path.read_text());body=[]
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name=='solve':break
 body.append(node)
class ReadOnly(ast.NodeTransformer):
 def visit_Expr(self,node):
  if isinstance(node.value,ast.Call):
   f=node.value.func
   if isinstance(f,ast.Name) and f.id in ['save','print']:return None
   if isinstance(f,ast.Attribute) and isinstance(f.value,ast.Name) and f.value.id=='np' and f.attr.startswith('save'):return None
  return self.generic_visit(node)
 def visit_Name(self,node):
  if node.id=='OUT':return ast.copy_location(ast.Name(id='OLD',ctx=node.ctx),node)
  return node
tree=ReadOnly().visit(ast.Module(body=body,type_ignores=[]));ast.fix_missing_locations(tree);st={'__file__':str(path),'__name__':'read_only_old_red_state'};argv=sys.argv[:];sys.argv=[str(path),'R','--all67','--robust','--hetero','--full-error-safe'];exec(compile(tree,str(path),'exec'),st);sys.argv=argv
names=st['names'];allframes={m['stem']:m for m in frames()};groups={}
for i,name in enumerate(names):groups.setdefault(allframes[name]['exp'],[]).append(i)
ids=[[],[]]
for exp,g in sorted(groups.items()):
 for j,i in enumerate(sorted(g,key=lambda i:allframes[names[i]]['time_C2'])):ids[j%2].append(i)
save('R4_protocol.json',dict(method=__doc__,halves=[[names[i] for i in ii] for ii in ids],bands=[12,16,24,40,64,96],orientations=8,gain='positive cross-power/(positive cross-power+half-difference power/4), applied to old full-data red detector',limits='Same sensor and calibration, not independent detectors. Source Sony/LROC and exact93 photographic claims unchanged. No new mask or stellar PSF.'))
W,Y,OW=st['W'],st['Y'],st['originalW'];filt,pull,push=st['filt'],st['pull'],st['push'];rad=st['rad'];Ns=N*N
for h,ii in enumerate(ids):
 den=W[ii].sum(0);base=sum(W[i]*Y[i] for i in ii)/np.maximum(den,1e-30);rhs=filt(sum(push(W[i]*(Y[i]-base),i) for i in ii));lm=.1*np.median(den[(rad<300)&(den>0)])
 def op(v):
  z=v.reshape(N,N);d=filt(z);pp=[pull(d,i) for i in ii];av=sum(W[i]*p for i,p in zip(ii,pp))/np.maximum(den,1e-30);return (filt(sum(push(W[i]*(p-av),i) for i,p in zip(ii,pp)))+lm*z).ravel()
 tic=time.time();count=[0]
 def cb(v):
  count[0]+=1
  if count[0]%5==0:print('RED HALF',h,count[0],round(time.time()-tic),flush=True)
 A=LinearOperator((Ns,Ns),matvec=op,dtype=np.float64);z,info=cg(A,rhs.ravel(),rtol=2e-5,maxiter=60,callback=cb);assert info==0;np.savez_compressed(OUT/f'arrays/R4_half{h}.npz',detector=filt(z.reshape(N,N)),iterations=count[0]);print('RED HALF DONE',h,flush=True)
a=rfft2(np.load(OUT/'arrays/R4_half0.npz')['detector']);b=rfft2(np.load(OUT/'arrays/R4_half1.npz')['detector']);fy=np.fft.fftfreq(N)[:,None];fx=np.fft.rfftfreq(N)[None,:];fr=np.hypot(fx,fy);ang=np.arctan2(fy,fx)%np.pi;gain=np.zeros(a.shape);rows=[]
for lo,hi in zip([12,16,24,40,64],[16,24,40,64,96]):
 for j in range(8):
  m=(fr>=1/hi)&(fr<1/lo)&(ang>=j*np.pi/8)&(ang<(j+1)*np.pi/8);sig=max(float(np.real(a[m]*b[m].conj()).sum()),0);noise=float((abs(a[m]-b[m])**2).sum()/4);g=sig/max(sig+noise,1e-30);gain[m]=g;rows.append(dict(band=[lo,hi],orientation=j,gain=g,cross_power=sig,noise_power=noise))
z=np.load(OLD/'arrays/B3_R67_robust_hetero_full_safe_all.npz');D=irfft2(rfft2(z['detector'])*gain,s=(N,N));correction=sum(OW[i]*pull(D,i) for i in range(len(names)))/np.maximum(OW.sum(0),1e-30);np.savez_compressed(OUT/'arrays/R4_repeatable_red.npz',detector=D,correction=correction,source=z['raw_baseline']-correction,raw_baseline=z['raw_baseline'],gain=gain);save('R4_repeatability.json',dict(rows=rows,source_sha256=sha(OUT/'arrays/R4_repeatable_red.npz'),status='Distinct source correction; external/photo/injection qualification pending'));print('RED REPEATABILITY DONE',flush=True)
