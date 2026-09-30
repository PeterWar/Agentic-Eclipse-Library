"""Frozen-weight source-domain injection through the assumed measured core.
Blind phases are drawn after model/regularization selection. This checks the
linear inverse operator only, not PSF truth, RAW calibration or CameraRaw.
"""
from optics_common import *
from scipy.fft import dctn,idctn
from scipy.sparse.linalg import LinearOperator,cg

metadata=json.loads((OUT/'B0_epoch_inverse.json').read_text());assert len(metadata['epochs'])==2
f=np.arange(N)/(2*N);freq2=f[:,None]**2+f[None,:]**2
lap=(4*np.sin(np.pi*f)**2)[:,None]+(4*np.sin(np.pi*f)**2)[None,:];L2=lap**2
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);rng=np.random.default_rng(1148123)
waves=[];wave_info=[]
for scale,angle in zip([8,16,24,40,64],[.17,.73,1.31,.43,1.07]):
    phase=float(rng.uniform(0,2*np.pi));waves.append(np.sin(2*np.pi*(x*np.cos(angle)+y*np.sin(angle))/scale+phase));wave_info.append(dict(scale=scale,angle=angle,phase=phase))
signal=sum(waves);rows=[]
for row in metadata['epochs']:
    epoch=row['epoch'];z=np.load(OUT/f'B0_{epoch}_inverse.npz');den=z['weight'];w=den/np.median(den);sigma=float(z['psf_sigma']);lam=float(z['lambda_normalized'])
    H=np.exp(-2*np.pi**2*sigma**2*freq2)
    def conv(a):return idctn(dctn(a,type=2,norm='ortho')*H,type=2,norm='ortho')
    def mv(v):
        a=v.reshape(N,N);return (conv(w*conv(a))+lam*idctn(dctn(a,type=2,norm='ortho')*L2,type=2,norm='ortho')).ravel()
    low=np.exp(-2*np.pi**2*4**2*freq2);Q=low/H;pre=(1-low**2)/(float(np.mean(w))*H**2+lam*L2)
    def pc(v):
        vh=dctn(v.reshape(N,N),type=2,norm='ortho');sm=idctn(vh*Q,type=2,norm='ortho')/w
        return idctn(dctn(sm,type=2,norm='ortho')*Q+vh*pre,type=2,norm='ortho').ravel()
    rhs=conv(w*conv(signal));op=LinearOperator((N*N,N*N),matvec=mv,dtype=np.float64);M=LinearOperator(op.shape,matvec=pc,dtype=np.float64);steps=[0]
    def cb(v):
        steps[0]+=1
        if steps[0]%300==0:print(epoch,'TRANSFER CG',steps[0],flush=True)
    v,info=cg(op,rhs.ravel(),x0=signal.ravel(),M=M,rtol=2e-6,atol=0,maxiter=1800,callback=cb)
    assert info==0,(epoch,info);answer=v.reshape(N,N);normal=float(np.linalg.norm(mv(v)-rhs.ravel())/np.linalg.norm(rhs));regions=[]
    for lo,hi in [(0,350),(350,435),(435,454)]:
        m=(r>=lo)&(r<hi);A=np.stack([s[m] for s in waves],1);gain=np.linalg.lstsq(A,answer[m],rcond=None)[0];error=float(np.sqrt(np.mean((answer[m]-signal[m])**2)/np.mean(signal[m]**2)));regions.append(dict(radius=[lo,hi],gain=gain.tolist(),relative_rms_error=error,PASS_90_110=bool(np.all((gain>=.9)&(gain<=1.1)))))
    np.savez_compressed(OUT/f'B2_{epoch}_response.npz',response=answer,signal=signal)
    rows.append(dict(epoch=epoch,lambda_normalized=lam,sigma=sigma,cg_iterations=steps[0],normal_relative_residual=normal,regions=regions));print(rows[-1],flush=True)
save('B2_transfer.json',dict(method=__doc__,seed=1148123,waves=wave_info,epochs=rows,PASS_operator_only=all(r['PASS_90_110'] for e in rows for r in e['regions']),limits=['Fixed source weights and assumed Gaussian core; neither are re-estimated during injection','No independent test of PSF model, source noise calibration or actual lunar texture','No RAW/CFA/CameraRaw end-to-end injection claim']))
