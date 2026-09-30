"""Native band-limited least-squares after unrestricted C2 overfit noise.
Scene correction on the existing grid; empirical per-frame polynomial nuisance
and total-error variance. Ridge selected using Vixen frame holdout only. Output
band is fixed16-64 with12-96 skirts, central pilot excludes64px boundaries.
"""
from common import *
from scipy.sparse import load_npz
from scipy.sparse.linalg import LinearOperator,cg
from scipy.ndimage import gaussian_filter
from scipy.fft import rfft2,irfft2
import time
claim();n=384;x0=y0=508;sl=np.s_[y0:y0+n,x0:x0+n];base=np.load(OLD/'arrays/B11_repeatable_all.npz')['source'][sl];rows=json.loads((OUT/'C1_native_matrices.json').read_text())['rows'];y,x=np.mgrid[:n,:n];theta=np.arctan2(y+y0-CY,x+x0-CX)%(2*np.pi);fit=((theta//(np.pi/6)).astype(int)%2)==0;valid=(x>=64)&(x<n-64)&(y>=64)&(y<n-64);hold=valid&~fit
protocol=dict(method=__doc__,ridge_grid=[.001,.01,.1],selection='Even-index Vixen frames fit, odd-index predict native sample residual; total error and six polynomial coefficients trained even spatial sectors against frozen V55. No Sony/LROC.',candidate='All-frame selected ridge; source plus smoothly band-limited native correction. No product/crop/mask modification.',injections='Frozen native operator/weights, independent sinusoidal12-96 source additions, baseline fixed; measure response and reject outside0.9-1.1 in pass band. Conditional operator test, not CameraRaw.',support='384 pilot, central256 only; full-disc reconstruction required before photographic use')
if (OUT/'C3_protocol.json').exists():assert json.loads((OUT/'C3_protocol.json').read_text())==protocol
else:save('C3_protocol.json',protocol)
fy=np.fft.fftfreq(n)[:,None];fx=np.fft.rfftfreq(n)[None,:];freq=np.hypot(fx,fy);u=np.clip((freq-1/96)/(1/64-1/96),0,1);v=np.clip((freq-1/16)/(1/12-1/16),0,1);H=(.5-.5*np.cos(np.pi*u))*(.5+.5*np.cos(np.pi*v))
def filt(v):return irfft2(rfft2(v.reshape(n,n))*H,s=(n,n)).ravel()
data=[];cal=[]
for j,row in enumerate(rows):
 A=load_npz(row['matrix']);z=np.load(row['samples_file']);p=z['xy'];px=(p[:,0]-CX)/n;py=(p[:,1]-CY)/n;Q=np.stack([np.ones(len(px)),px,py,px*px,px*py,py*py],1);th=np.arctan2(py,px)%(2*np.pi);tr=(th//(np.pi/6)).astype(int)%2==0;v=z['variance'];q=z['quality'];err=z['observed']-z['reference_prediction'];w=q/np.maximum(v,1e-12);cf=np.linalg.lstsq(Q[tr]*np.sqrt(w[tr,None]),err[tr]*np.sqrt(w[tr]),rcond=None)[0];e=err-Q@cf
 # The extra variance is measured on training sectors only, one scalar/frame;
 # it cannot assign local pixel masks or follow lunar features.
 extra=max(float(np.average(e[tr]**2,weights=q[tr])-np.average(v[tr],weights=q[tr])),0);w=q/np.maximum(v+extra,1e-12);data.append((A,e,w));cal.append(dict(stem=row['stem'],nuisance=cf,extra_variance=extra,residual_rms=float(np.std(e)),native_samples=len(e)))
scale=float(np.median(sum(np.asarray(A.T@w).ravel() for A,e,w in data)));data=[(A,e,w/scale) for A,e,w in data]
def solve(ids,lam,values=None):
 diag=sum(np.asarray(A.power(2).T@w).ravel() for i,(A,e,w) in enumerate(data) if i in ids)+lam
 rhs=sum(np.asarray(A.T@(w*(e if values is None else values[i]))).ravel() for i,(A,e,w) in enumerate(data) if i in ids)
 def mv(v):return lam*v+sum(np.asarray(A.T@(w*(A@v))).ravel() for i,(A,e,w) in enumerate(data) if i in ids)
 rhs=filt(rhs)
 def bandmv(v):return lam*v+filt(sum(np.asarray(A.T@(w*(A@filt(v)))).ravel() for i,(A,e,w) in enumerate(data) if i in ids))
 op=LinearOperator((n*n,n*n),matvec=bandmv);pre=LinearOperator(op.shape,matvec=lambda v:irfft2(rfft2(v.reshape(n,n))/(lam+H*H*sum(float(w.sum()) for i,(A,e,w) in enumerate(data) if i in ids)/(n*n)),s=(n,n)).ravel());ans,info=cg(op,rhs,M=pre,rtol=1e-7,maxiter=150);assert info==0,info
 return filt(ans).reshape(n,n)
train=list(range(0,len(data),2));test=list(range(1,len(data),2));scores=[];tic=time.time()
for lam in [.001,.01,.1]:
 delta=solve(train,lam);score=sum(float(np.sum(w*(e-A@delta.ravel())**2)) for i,(A,e,w) in enumerate(data) if i in test)/sum(float(w.sum()) for i,(A,e,w) in enumerate(data) if i in test);scores.append(dict(ridge=lam,heldout_native_mse=score));print('NATIVE FIT',lam,score,round(time.time()-tic),flush=True)
lam=min(scores,key=lambda a:a['heldout_native_mse'])['ridge'];delta=solve(list(range(len(data))),lam);fy=np.fft.fftfreq(n)[:,None];fx=np.fft.rfftfreq(n)[None,:];freq=np.hypot(fx,fy);u=np.clip((freq-1/96)/(1/64-1/96),0,1);v=np.clip((freq-1/16)/(1/12-1/16),0,1);H=(.5-.5*np.cos(np.pi*u))*(.5+.5*np.cos(np.pi*v));filtered=delta;candidate=base+filtered
np.savez_compressed(OUT/'arrays/C3_native_pilot.npz',baseline=base,candidate=candidate,delta=delta,filtered=filtered,valid=valid)
injections=[]
for period in [16,24,40,64]:
 for angle in [0,np.pi/3]:
  wave=np.sin(2*np.pi*(x*np.cos(angle)+y*np.sin(angle))/period+.719);ans=solve(list(range(len(data))),lam,[A@wave.ravel() for A,e,w in data]);vv=wave[valid];gain=float(vv@ans[valid]/(vv@vv));injections.append(dict(period=period,angle=angle,gain=gain,rms_error=float(np.std((ans-wave)[valid]))))
sony=np.load(ROOT/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'][sl];lc=np.load(ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];lr=np.zeros((N,N));oy,ox=bb[1]-Y0,bb[0]-X0;lr[oy:oy+lc.shape[0],ox:ox+lc.shape[1]]=lc[...,:3].mean(-1);win=np.hanning(n)[:,None]*np.hanning(n)[None,:];Q=np.stack([np.ones_like(x),x/n,y/n],-1)
def transform(a):
 co=np.linalg.lstsq(Q.reshape(-1,3)*win.ravel()[:,None],a.ravel()*win.ravel(),rcond=None)[0];return rfft2((a-Q@co)*win)
F={k:transform(a) for k,a in dict(V55source=base,native=candidate,Sony=sony,LROC=lr[sl]).items()};judge=[]
for lo,hi in [(8,16),(16,24),(24,40),(40,64),(64,96)]:
 m=(freq>=1/hi)&(freq<1/lo);b={k:irfft2(f*m,s=(n,n)) for k,f in F.items()}
 for k in ['V55source','native']:
  j=dict(band=[lo,hi],candidate=k,Sony=corr(b[k],b['Sony'],hold),LROC=corr(b[k],b['LROC'],hold));judge.append(j);print('NATIVE JUDGE',j,flush=True)
save('C3_native_pilot.json',dict(calibration=cal,ridge_scores=scores,selected_ridge=lam,injections=injections,judge=judge,limits=['Conditional source operator; no new optical resolution','Central pilot, full-field validation pending','Total-error covariance is empirical, independent captures share calibration']))
