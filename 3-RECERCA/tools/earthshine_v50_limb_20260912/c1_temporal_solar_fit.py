"""Temporal PSF calibration from occulted solar fields, without a flat Moon assumption.
The common lunar field cancels between early/late complete stacks. Fit kernel
coefficients from their difference on alternating sectors, never from making
one Moon flat. Solar estimates are positive C0 source exterior reconstructions.
Terminal 6px and alternate sectors are held out. Experimental only.
"""
from common50 import *
from scipy.fft import rfft2,irfft2
from scipy.optimize import minimize
from scipy.ndimage import gaussian_filter
import time
sig=np.array([.7,.9,1.1,1.4,2.,4.,8.,16.,32.,64.,128.]);Y,X=np.mgrid[:N,:N];r=np.hypot(X-CX,Y-CY);th=np.arctan2(Y-CY,X-CX)%(2*np.pi);sec=(th*24/(2*np.pi)).astype(int)
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');d=r-np.interp(th,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi)
kx=np.fft.rfftfreq(N)[None,:];ky=np.fft.fftfreq(N)[:,None];f2=kx*kx+ky*ky
Ts=[np.exp(-2*np.pi**2*(s*s+1/3+1/12)*f2) for s in sig]
Z={g:dict(np.load(OUT/f'C0_stack_{g}.npz')) for g in ['early','late','all']};G={g:np.load(ROOT/f'output/earthshine_native_psf_20260911/B0_new_{g}.npz')['candidate'] for g in Z}
C={}
for g,z in Z.items():
 F=rfft2(z['solar']*(1-z['mask']));C[g]=np.array([irfft2(F*T,s=(N,N)) for T in Ts]);print('BASIS',g,flush=True)
D=G['early']-G['late'];deep=r<350;planeA=np.c_[np.ones(deep.sum()),(X[deep]-CX)/455,(Y[deep]-CY)/455];cf=np.linalg.lstsq(planeA,D[deep],rcond=None)[0];D-=cf[0]+cf[1]*(X-CX)/455+cf[2]*(Y-CY)/455
# 5x5 mean cells suppress measurement noise; averaging never writes source radiance.
def reduce(a):return a.reshape(*a.shape[:-2],N//5,5,N//5,5).mean(axis=(-3,-1))
Dcell=reduce(D);B=reduce(C['early']-C['late']).reshape(len(sig),-1).T;dc=reduce(d).ravel();rc=reduce(r).ravel();sc=sec[2::5,2::5].ravel();use=(rc>350)&(dc<-6)&(rc<449);train=use&(sc%2==0);val=use&(sc%2==1);last=(dc>=-6)&(dc<-.5)
y=Dcell.ravel();scale=np.maximum(reduce(np.maximum(G['early'],0)+np.maximum(G['late'],0)).ravel(),500)**-.5
A=B[train]*scale[train,None];b=y[train]*scale[train]
p0=np.zeros(len(sig));p0[2]=.83;p0[4]=.1;p0[5]=.045;p0[6]=.009;p0[7]=.01;p0[8]=.006;p0/=p0.sum()
baseline=np.mean(b*b)
def objective(p):
 e=A@p-b;return np.mean(e*e)/baseline,2*A.T@e/len(e)/baseline
opt=minimize(objective,p0,jac=True,method='SLSQP',bounds=[(0,1)]*len(sig),constraints=[dict(type='eq',fun=lambda p:p.sum()-1,jac=lambda p:np.ones(len(p)))],options=dict(maxiter=500,ftol=1e-12))
p=opt.x;res=y-B@p;checks={}
for name,m in [('train',train),('heldout',val),('last6',last)]:checks[name]=dict(before=float(np.sqrt(np.mean(y[m]**2))),after=float(np.sqrt(np.mean(res[m]**2))))
for g in Z:
 spill=np.einsum('k,kij->ij',p,C[g]);np.savez_compressed(OUT/f'C1_temporal_{g}.npz',spill=spill,corrected=G[g]-spill)
save('C1_temporal_result.json',dict(method=__doc__,sigma=sig.tolist(),p=p.tolist(),success=bool(opt.success),message=str(opt.message),checks=checks,plane=cf.tolist(),publication=False))
print(p,checks,flush=True)
