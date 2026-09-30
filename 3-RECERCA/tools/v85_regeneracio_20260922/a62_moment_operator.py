"""Quadratic moment-matched Gaussian mean on observed support, local boundary only.
No ridge, clipping, interior image synthesis or data edits. Experimental E3.
"""
from a13_filters import *
from scipy.ndimage import minimum_filter
POW=[(0,0),(1,0),(0,1),(2,0),(1,1),(0,2)]
SIGMAS=[1,2,4,8,16,32,48,64]

def setup():
 z=np.load(O/'current_lunar_support.npz');x0,y0,x1,y1=map(int,z['box']);roi=(slice(y0-700,y1+700),slice(x0-700,x1+700));m=np.asarray(np.load(O/'domain_v1/sources/support.npy',mmap_mode='r')[roi]);assert m.shape==(2800,2800);return roi,m

def kernels(s):
 radius=int(4*s);g=cv2.getGaussianKernel(2*radius+1,s,cv2.CV_64F).ravel();u=np.arange(-radius,radius+1,dtype=float)/s;return [g*u**p for p in range(5)],radius

def sep(a,p,q,kk):
 return cv2.sepFilter2D(a,cv2.CV_64F,kk[p],kk[q],borderType=cv2.BORDER_REFLECT_101)

def build():
 out=O/'moment_E3_R02';out.mkdir();(out/'coefficients').mkdir();roi,m=setup();md=m.astype(float);save(out/'FROZEN_METHOD.json',{'domain':'same domain_v1 physical exterior excluding final photographic Moon, as R01; no input photometry change','purpose':'numerical boundary comparison against R01, not a claim photo mask is unique physical support','basis':POW,'u_v':'kernel offsets divided by sigma','target':'full discrete Gaussian mean, mu=[1,0,0,mu2,0,mu2], NOT polynomial value at central pixel','equations':'M=sum k*m*phi*phiT; b=sum k*m*phi*L; output=muT*solve(M,b)','gaussian':'installed OpenCV float32 automatic radius4sigma; use exact discrete kernels and original output at complete stencils','degree':2,'sigmas':SIGMAS,'regularization':None,'clipping':False,'fallback':None,'condition_guard':'whitened M eigenvalues positive and condition<1e8, chosen numerical safety not image tuning','scope':'E3 pre-display null/injection pilot first; no PSB change or sciencePASS','roi_y0y1x0x1':[roi[0].start,roi[0].stop,roi[1].start,roi[1].stop]});receipts=[]
 for s in SIGMAS:
  kk,radius=kernels(s);complete=minimum_filter(m,size=2*radius+1,mode='reflect');active=m&~complete;iy,ix=np.where(active);moments={(p,q):sep(md,p,q,kk)[iy,ix] for p in range(5) for q in range(5-p)};full={(p,q):float(kk[p].sum()*kk[q].sum()) for p in range(5) for q in range(5-p)};F=np.array([[full[(p+u,q+v)] for u,v in POW] for p,q in POW]);mu=F[:,0];B=np.linalg.inv(np.linalg.cholesky(F));alpha=np.empty((len(iy),6));condition=[];quaderr=0.;masserr=0.;eigmin=[]
  for start in range(0,len(iy),20000):
   end=min(start+20000,len(iy));M=np.stack([moments[(p+u,q+v)][start:end] for p,q in POW for u,v in POW],axis=1).reshape(-1,6,6);MW=B@M@B.T;ev=np.linalg.eigvalsh(MW);cond=ev[:,-1]/ev[:,0];assert np.all(ev[:,0]>0) and np.max(cond)<1e8,(s,ev.min(),cond.max());aa=np.linalg.solve(M,np.broadcast_to(mu,(len(M),6))[...,None])[...,0];alpha[start:end]=aa;res=np.einsum('ni,nij->nj',aa,M)-mu;quaderr=max(quaderr,float(np.max(abs(res))));condition.append(cond);eigmin.append(float(ev[:,0].min()))
  # Polynomial moment identities plus explicit image-polynomial check below.
  assert quaderr<1e-9;(out/'coefficients'/str(s)).mkdir();np.save(out/'coefficients'/str(s)/'indices.npy',np.stack([iy,ix]).astype(np.int32));np.save(out/'coefficients'/str(s)/'alpha.npy',alpha);row={'sigma':s,'affected_observed_pixels':len(iy),'condition_percentiles_0_50_95_100':np.percentile(np.concatenate(condition),[0,50,95,100]).tolist(),'whitened_min_eigenvalue':min(eigmin),'moment_identity_max_error':quaderr,'mu':mu.tolist(),'alpha_sha256':sha(out/'coefficients'/str(s)/'alpha.npy')};receipts.append(row);save(out/'PROGRESS.json',receipts);print('MOMENT_COEFFICIENT',s,len(iy),row['condition_percentiles_0_50_95_100'][-1],flush=True);del moments,alpha,condition;gc.collect()
 save(out/'COEFFICIENTS_COMPLETE.json',{'PASS':True,'rows':receipts,'scope':'numerical moment identity and conditioning only'})

class MomentGaussian:
 def __init__(self):
  self.roi,self.m=setup();self.folder=O/'moment_E3_R02';assert json.loads((self.folder/'COEFFICIENTS_COMPLETE.json').read_text())['PASS'];self.cache={}
 def smooth_roi(self,a,s,ordinary=None):
  if s not in self.cache:
   p=self.folder/'coefficients'/str(s);self.cache[s]=(np.load(p/'indices.npy'),np.load(p/'alpha.npy'))
  (iy,ix),alpha=self.cache[s];kk,_=kernels(s);weighted=np.where(self.m,a,0).astype(float);result=np.array(ordinary if ordinary is not None else cv2.GaussianBlur(np.asarray(a,np.float32),(0,0),s,borderType=cv2.BORDER_REFLECT_101),dtype=np.float64);estimate=np.zeros(len(iy),float)
  for j,(p,q) in enumerate(POW):estimate+=alpha[:,j]*sep(weighted,p,q,kk)[iy,ix]
  assert np.isfinite(estimate).all();result[iy,ix]=estimate;return result
 def install(self,ns):
  original=ns['normgauss']
  def adapted(a,w,s):
   result=original(a,w,s)
   # The new estimator applies only to the unweighted pre-display E3 bands.
   # Weighted post-display S/N smoothing retains its original operator.
   if not np.all(w[self.roi]==1):return result
   corrected=self.smooth_roi(a[self.roi],s,result[self.roi]);result[self.roi]=corrected.astype(result.dtype);return result
  ns['normgauss']=adapted

if __name__=='__main__':guard();build()
