"""Joint source model: one lunar field, a separate solar field per capture.

The preliminary single-frame optical split leaves large edge residuals and is
NOT accepted. This joint fit permits the exterior to change with time while
the registered lunar field is shared. Fit/source outputs are experimental.
Measured green values are mapped once to the existing 1400 grid; the forward
PSF includes the average interpolation variance, a declared approximation that
must survive heldout observations and injection before any final promotion.
"""
from common50 import *
from optical_matte import coordinates
from scipy.ndimage import map_coordinates
from scipy.fft import rfft2,irfft2
import time

fit=json.loads((OUT/'A1_fit.json').read_text());p=np.array(fit['p'])
star=json.loads((OUT/'B0_native_star_psf.json').read_text());core=star['core_sigma_native_percentiles'][1]
stems=[r['stem'] for r in fit['training']]
yy,xx=np.mgrid[:N,:N];world=np.stack([xx,yy],-1);r=np.hypot(xx-CX,yy-CY)
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
M=np.zeros((N,N))
for oy in [-.375,-.125,.125,.375]:
    for ox in [-.375,-.125,.125,.375]:
        th=np.arctan2(yy+oy-CY,xx+ox-CX)%(2*np.pi);lim=np.interp(th,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi)
        M+=(np.hypot(xx+ox-CX,yy+oy-CY)<lim)/16
O=1-M;deep=r<350;A=np.stack([np.ones(deep.sum()),(xx[deep]-CX)/455,(yy[deep]-CY)/455],1)
data=[];planes=[];vars=[]
for stem in stems:
    z=dict(np.load(NATIVE/f'D0_native_field_{stem}.npz'));assert np.all(z['valid'])
    native=(world-z['world_origin'])@np.linalg.inv(z['native_to_world']).T;u=(native[...,0]+native[...,1]-1)/2-int(z['u0']);v=(native[...,0]-native[...,1]-1)/2-int(z['v0'])
    g=map_coordinates(z['g'],[v,u],order=1,mode='nearest',prefilter=False)
    # Exact bilinear variance of independent native samples, not interpolated variance.
    iu=np.floor(u).astype(int);iv=np.floor(v).astype(int);fu=u-iu;fv=v-iv;var=np.zeros_like(g)
    for dv,du,b in [(0,0,(1-fu)*(1-fv)),(0,1,fu*(1-fv)),(1,0,(1-fu)*fv),(1,1,fu*fv)]:var+=b*b*z['variance'][iv+dv,iu+du]
    cf=np.linalg.lstsq(A,g[deep],rcond=None)[0];plane=cf[0]+cf[1]*(xx-CX)/455+cf[2]*(yy-CY)/455
    data.append(g-plane);planes.append(plane);vars.append(var);print('REGISTERED',stem,flush=True)
D=np.array(data);B=np.array(planes);W=1/np.maximum(np.array(vars),1e-9);W/=max(float(np.percentile(w[deep],99)) for w in W);W=np.minimum(W,1)
np.savez_compressed(OUT/'B2_joint_inputs.npz',g=D+B,background=B,weight=W,mask=M)
kx=np.fft.rfftfreq(N)[None,:];ky=np.fft.fftfreq(N)[:,None];f2=kx*kx+ky*ky
T=np.full(f2.shape,1-p.sum())
for coefficient,sigma in zip(p,SIGMA):T+=coefficient*np.exp(-2*np.pi**2*sigma*sigma*f2)
T*=np.exp(-2*np.pi**2*(core*core+1/3)*f2)
J=z['native_to_world'];T*=np.sinc(J[0,0]*kx+J[1,0]*ky)*np.sinc(J[0,1]*kx+J[1,1]*ky)
def blur(a):return irfft2(rfft2(a,workers=2)*T,s=(N,N),workers=2)
inv=T/(T*T+.003*(4*f2)**2+1e-30)
S=np.maximum(irfft2(rfft2(D,workers=2)*inv,s=(N,N),workers=2),0)*O
L=np.zeros((N,N));YL=L.copy();YS=S.copy();t=1.;history=[]
step_s=.45;step_l=.45/max(sum(float(w.max()) for w in W),1e-9)
save('B2_joint_plan.json',dict(method=__doc__,stems=stems,p=p.tolist(),core_sigma=core,interpolation_variance_per_axis=1/3,mask='Frozen Vixen observed contour with 4x4 area coverage; not a changed Photoshop mask',optimization='Projected FISTA,120 iterations, solar>=0 outside, shared lunar signed residual inside. Background planes fit r<350 per capture; source output retains original background.',step_solar=step_s,step_lunar=step_l,limits='Mean interpolation PSF and frozen observed boundary are approximations. This fit has no independent validation yet. Single-frame B1 pilot rejected as final.'))
start=time.time()
for iteration in range(120):
    pred=blur(M*YL+O*YS);res=pred-D;back=blur(W*res)
    Ln=YL-step_l*M*back.sum(axis=0);Sn=np.maximum(YS-step_s*O*back,0)
    tn=(1+np.sqrt(1+4*t*t))/2;YL=Ln+(t-1)/tn*(Ln-L);YS=Sn+(t-1)/tn*(Sn-S);L=Ln;S=Sn;t=tn
    if iteration%10==0 or iteration==119:
        obj=float(np.sum(W*res*res)/np.sum(W));row=dict(iteration=iteration,objective=obj,seconds=time.time()-start);history.append(row);save('B2_joint_progress.json',dict(history=history));print('JOINT',iteration,round(obj,3),round(time.time()-start,1),'s',flush=True)
        np.savez_compressed(OUT/'B2_joint_checkpoint.npz',lunar=L,solar=S,iteration=iteration)
spill=blur(O*S);corrected=D+B-spill
np.savez_compressed(OUT/'B2_joint_result.npz',lunar=L,solar=S,spill=spill,corrected=corrected,mask=M,transfer=T)
np.save(OUT/'B2_mean_spill.npy',np.sum(W*spill,axis=0)/np.maximum(W.sum(axis=0),1e-30))
save('B2_joint_result.json',dict(method=__doc__,stems=stems,history=history,core_sigma=core,publication='NONE; validation and visual review pending'))
print('JOINT COMPLETE',flush=True)
