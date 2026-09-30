"""One global, masked spatial self-calibration problem; no tiling/mosaic.
Scene eliminated analytically; detector field is a Fourier-band-limited
latent on the full1400 grid. Exact bilinear translation adjoints. Only
observed lunar support enters loss; no exterior corona enters the FFT data.
"""
from common import *
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from scipy.fft import rfft2,irfft2
from scipy.sparse.linalg import LinearOperator,cg
import time,sys
claim();design=json.loads((OUT/'B0_fpn_design.json').read_text());plan=json.loads((OUT/'PLAN.json').read_text());sh=np.array(design['shifts_common']);names=design['names'];chan=sys.argv[1] if len(sys.argv)>1 else 'G'
assert chan in ['G','R','B'];outprefix='B3_'+chan
if '--all67' in sys.argv:
    rows=[q for q in json.loads((OUT/'A1_native_rgb_all.json').read_text())['frames'] if q['tren']=='vixen'];names=[q['stem'] for q in rows]
    A0=np.array(rows[0]['roi_to_native']);centres=np.array([np.array(q['roi_to_native'])@np.array([CX,CY,1]) for q in rows]);sh=(np.linalg.inv(A0[:,:2])@(centres-centres[0]).T).T
    outprefix+='67'
robust='--robust' in sys.argv
if robust:outprefix+='_robust'
hetero='--hetero' in sys.argv
assert not hetero or robust
if hetero:outprefix+='_hetero'
full_error='--full-error' in sys.argv or '--full-error-safe' in sys.argv
assert not full_error or hetero
if full_error:outprefix+='_full'
if '--full-error-safe' in sys.argv:outprefix+='_safe'
rad,theta=geometry();edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');edge=gaussian_filter1d(edge,3,mode='wrap');er=np.interp(theta,np.linspace(0,2*np.pi,len(edge),endpoint=False),edge,period=2*np.pi);physical=rad<er
yy,xx=np.mgrid[:N,:N];x=(xx-CX)/455;y=(yy-CY)/455;basis=np.stack([x**i*y**j for i in range(4) for j in range(4-i)],-1);lowfit=(rad<410)&((theta//(np.pi/6)).astype(int)%2==0)
fy=np.fft.fftfreq(N)[:,None];fx=np.fft.rfftfreq(N)[None,:];f=np.hypot(fx,fy)
u=np.clip((f-1/96)/(1/64-1/96),0,1);v=np.clip((f-1/16)/(1/12-1/16),0,1);H=(.5-.5*np.cos(np.pi*u))*(.5+.5*np.cos(np.pi*v))
def filt(a):return irfft2(rfft2(a)*H,s=(N,N))
maps=[]
for sx,sy in sh:
    ix=int(np.floor(sx));iy=int(np.floor(sy));qx=sx-ix;qy=sy-iy
    maps.append([(iy,ix,(1-qy)*(1-qx)),(iy,ix+1,(1-qy)*qx),(iy+1,ix,qy*(1-qx)),(iy+1,ix+1,qy*qx)])
def pull(a,i):return sum(w*np.roll(a,(-dy,-dx),(0,1)) for dy,dx,w in maps[i])
def push(a,i):return sum(w*np.roll(a,(dy,dx),(0,1)) for dy,dx,w in maps[i])
# Numerical adjoint validation is consequential: a non-adjoint reverse warp
# can masquerade as successful self-calibration.
rng=np.random.default_rng(551309);aa=rng.normal(size=(N,N));bb=rng.normal(size=(N,N));adj=[]
for i in [0,2,6,11]:adj.append(float(abs(np.sum(pull(aa,i)*bb)-np.sum(aa*push(bb,i)))/max(abs(np.sum(pull(aa,i)*bb)),1)))
assert max(adj)<1e-10;del aa,bb
save(outprefix+'_design.json',dict(method=__doc__,channel=chan,names=names,shifts=sh,ridge=.1,band=dict(passband=[16,64],skirts=[12,96],operator='raised cosine radial Fourier transfer on entire1400 plane'),mask='Physical observed lunar limb plus individual CFA saturation/validity; no photographic alpha changes',low_frequency_nuisance='Per-frame cubic of deviation from starting weighted mean, even sectors r<410; used to estimate detector only, not subtracted from product',adjoint_relative_errors=adj,planned=['train-only fit and all-pilot fit','unchanged temporal reserved and Sony/LROC','actual-space scene and detector injection'],limitations=['Registered interpolation at ordinary G resolution, not CFA super-resolution','Constant detector model is calibrated radiance approximation; no physical dark/flat claim beyond heldout proof']))
Y=[];W=[];nr=[]
for i,stem in enumerate(names):
    z=np.load(OUT/'native'/('vixen_'+stem+'.npz'))
    if chan=='G':
        q=(z['G1_q']+z['G2_q'])/2;a=(np.nan_to_num(z['G1'])*z['G1_q']+np.nan_to_num(z['G2'])*z['G2_q'])/np.maximum(2*q,1e-30)
        vv=(np.nan_to_num(z['G1_var'])*z['G1_q']**2+np.nan_to_num(z['G2_var'])*z['G2_q']**2)/np.maximum((2*q)**2,1e-30)
    else:a=z[chan];q=z[chan+'_q'];vv=z[chan+'_var']
    good=np.isfinite(a)&np.isfinite(vv)&(q>0)&physical;vs=gaussian_filter(np.where(good,vv,0),4)/np.maximum(gaussian_filter(good.astype(float),4),1e-30)
    w=np.where(good,q/np.maximum(vs,1e-12),0);Y.append(np.where(good,a,0));W.append(w)
Y=np.array(Y,dtype=np.float64);W=np.array(W,dtype=np.float64);den=W.sum(0);base=np.sum(Y*W,axis=0)/np.maximum(den,1e-30);poly=[]
train=np.array([s in plan['pilot']['fit_vixen'] for s in names])
nuisance_ref=np.sum(Y[train]*W[train],axis=0)/np.maximum(W[train].sum(0),1e-30) if robust else base
for i in range(len(names)):
    m=lowfit&(W[i]>0);wt=np.sqrt(W[i,m]);co=np.linalg.lstsq(basis[m]*wt[:,None],(Y[i,m]-nuisance_ref[m])*wt,rcond=None)[0];poly.append(co)
    Y[i]-=basis@co
del basis;originalW=W.copy() if robust else W
if robust:
    td=W[train].sum(0);tb=np.sum(Y[train]*W[train],axis=0)/np.maximum(td,1e-30);vsys=np.zeros((N,N));ld=np.zeros((N,N))
    for i in np.flatnonzero(train):
        dw=gaussian_filter(W[i],32);lp=gaussian_filter(W[i]*(Y[i]-tb),32)/np.maximum(dw,1e-30);vsys+=dw*lp**2;ld+=dw
    vsys/=np.maximum(ld,1e-30)
    row=[]
    for lo,hi in [[60,250],[250,350],[350,410],[410,435],[435,450]]:
        m=(rad>=lo)&(rad<hi);row.append(dict(radius=[lo,hi],low_temporal_rms_G=float(np.sqrt(np.median(vsys[m])))))
    if hetero:
        # Exposure-specific broad mismatch is a measured nuisance, not a
        # detector field. Estimate only low frequencies of each frame's
        # residual; reference and polynomial basis fixed to training captures.
        # This uses per-frame nuisance information, so temporal prediction
        # must be labelled conditional, not a fully untouched raw holdout.
        summary=[]
        for i in range(len(names)):
            dw=gaussian_filter(W[i],32);lp=gaussian_filter(W[i]*(Y[i]-tb),32)/np.maximum(dw,1e-30);localvar=vsys+lp**2
            if full_error:
                # A steep changing limb is not confined to low Fourier modes.
                # Use local mean-square prediction error, estimated without
                # self-reference for training frames. No lunar radius cutoff.
                if train[i]:
                    remain=td-originalW[i]
                    ri=np.divide(td*tb-originalW[i]*Y[i],remain,out=Y[i].copy(),where=remain>1e-12)
                else:ri=tb
                localvar=vsys+gaussian_filter(originalW[i]*(Y[i]-ri)**2,32)/np.maximum(dw,1e-30)
            summary.append(dict(stem=names[i],median_variance_inner=float(np.median(localvar[rad<350])),median_variance_limb=float(np.median(localvar[(rad>435)&(rad<449)]))))
            W[i]=W[i]/(1+W[i]*localvar)
        save(outprefix+'_frame_error_model.json',dict(rule='W_i/(1+W_i*(training low-frequency variance + local total mean-square prediction error)); sigma32, leave-self-out training reference, no radius selection.' if full_error else 'W_i/(1+W_i*(training low-frequency variance + individual low-frequency residual squared)); sigma32, no radius selection. FPN and science bands remain Fourier.',frames=summary,limits='Per-frame nuisance is measured on each source, including reserved captures; temporal residual after this step is CONDITIONAL. External Sony/LROC and blind scene/detector tests remain unchanged. No use of external pixels to choose weights. Full-error includes some true FPN as conservative covariance; it does not subtract that variance from image pixels.'))
    else:W=W/(1+W*vsys[None,:,:])
    np.save(OUT/'arrays'/(outprefix+'_variance_field.npy'),vsys.astype(np.float32))
    save(outprefix+'_covariance_design.json',dict(rule='Add variance of per-frame LOW-frequency temporal residual (normalized Gaussian sigma32) to conditional photon variance; seven training captures only. Wnew=Wold/(1+Wold*vsys). No angular/radial gate or Photoshop mask.',rows=row,baseline='Original photon-weighted source held fixed; only detector estimate subtracted using original source weights',qualification='New error-model branch. Earlier full-field residual-FFT numbers are contaminated by masked edge discontinuity and are not a valid limb metric; use supported local spectra/physical residuals for judging. No prior thresholds redefined.'))
    print('COVARIANCE',chan,row,flush=True)
lam=.1*np.median(den[(rad<300)&(den>0)]);progress=[]
def solve(ids,label):
    deni=W[ids].sum(0);basei=np.sum(W[ids]*Y[ids],axis=0)/np.maximum(deni,1e-30)
    rhs=sum(push(W[i]*(Y[i]-basei),i) for i in ids);rhs=filt(rhs);lm=.1*np.median(deni[(rad<300)&(deni>0)])
    def op(v):
        latent=v.reshape(N,N);D=filt(latent);pp=[pull(D,i) for i in ids];avg=sum(W[i]*p for i,p in zip(ids,pp))/np.maximum(deni,1e-30)
        result=sum(push(W[i]*(p-avg),i) for i,p in zip(ids,pp));return (filt(result)+lm*latent).ravel()
    counter=[0];tic=time.time()
    def callback(v):
        counter[0]+=1
        if counter[0]%5==0:print('CG',chan,label,counter[0],'seconds',round(time.time()-tic),flush=True)
    A=LinearOperator((N*N,N*N),matvec=op,dtype=np.float64);latent,info=cg(A,rhs.ravel(),rtol=2e-5,maxiter=60,callback=callback);D=filt(latent.reshape(N,N));res=np.linalg.norm(op(latent)-rhs.ravel())/max(np.linalg.norm(rhs),1e-30)
    assert info==0 and res<3e-5,(info,res);predD=[pull(D,i) for i in range(len(names))];correction=sum(W[i]*predD[i] for i in ids)/np.maximum(deni,1e-30)
    scene=basei-correction
    product_correction=sum(originalW[i]*predD[i] for i in ids)/np.maximum(originalW[ids].sum(0),1e-30)
    # Reserved loss weighted by conditional noise. The nuisance coefficients
    # are separate low-frequency fits, so compare only band-passed residuals.
    errs={}
    for kind in ['baseline','model']:
        vals=[]
        for i in range(len(names)):
            residual=Y[i]-(basei if kind=='baseline' else scene+predD[i]);b=filt(np.where(physical,residual,0));m=(rad<410)&(W[i]>0)
            vals.append(float(np.sum(W[i,m]*b[m]**2)/np.sum(W[i,m])))
        errs[kind]=vals
    np.savez_compressed(OUT/'arrays'/(outprefix+'_'+label+'.npz'),detector=D,correction=product_correction,source=base-product_correction,raw_baseline=base,model_scene=scene,denominator=deni)
    return dict(label=label,indices=ids,iterations=counter[0],relative_residual=res,losses=errs,central_correction_rms=float(np.std(correction[rad<350])),ridge_absolute=lm)
for ids,label in [(np.flatnonzero(train),'train'),(np.arange(len(names)),'all')]:progress.append(solve(ids,label))
save(outprefix+'_result.json',dict(channel=chan,solves=progress,nuisance_coefficients=poly,adjoint_errors=adj,model_is_physical_FPN='Supported by central pilot only so far; full-disc external/injection qualification pending'))
print('B3 DONE',chan,flush=True)
