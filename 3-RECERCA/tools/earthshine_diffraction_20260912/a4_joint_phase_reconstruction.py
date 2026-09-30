"""Numerical qualification of joint four-alias inversion at the measured phases.
No seeing-power prior: solve four complex Fourier coefficients jointly before
dividing by the independently specified pupil OTF. The common scene, exact
registration and periodic boundary are synthetic assumptions, not real-data facts.
"""
from diffraction_common import *
from scipy.fft import rfftn, irfftn, fft2, ifft2, fftfreq, rfftfreq
from scipy.ndimage import map_coordinates
import time

frames=json.loads((OUT/'A2_stack_plan.json').read_text())['frames']
N=256; OVER=8; FINE=N*OVER
f=fftfreq(N); fv0=f[:,None]; fu0=f[None,:]
fv=fftfreq(FINE,d=1/OVER)[:,None];fu=rfftfreq(FINE,d=1/OVER)[None,:]
freq=np.hypot(fu,fv)/np.sqrt(2)
Hc=np.exp(-2*np.pi**2*.97**2*freq**2)
Hp=np.sinc((fu+fv)/2)*np.sinc((fu-fv)/2)
V,U=np.meshgrid(np.arange(FINE)/OVER-N/2,np.arange(FINE)/OVER-N/2,indexing='ij')
J=np.array(frames[0]['J']);X=J[0,0]*(U+V)+J[0,1]*(U-V);Y=J[1,0]*(U+V)+J[1,1]*(U-V)
P=np.hypot(X,Y)<120
baseline=np.where(P,650,100000+70000*np.exp(-((X-124)**2+(Y-9)**2)/(2*8**2)))
wy,wx=np.mgrid[-140:141,-140:141].astype(float);wr=np.hypot(wx,wy);test=(wr>=100)&(wr<119)
nxy=np.stack([wx.ravel(),wy.ravel()],1)@np.linalg.inv(J).T
uw=(nxy[:,0]+nxy[:,1])/2;vw=(nxy[:,0]-nxy[:,1])/2
parts={key:[r for r in frames if key=='all' or r['half']==key] for key in ['all','early','late']}
groups=[]
for signv in [-1,1]:
    for signu in [-1,1]:
        mask=((fv0>=0) if signv==-1 else (fv0<0)) & ((fu0>=0) if signu==-1 else (fu0<0))
        aliases=[(0,0),(signu,0),(0,signv),(signu,signv)]
        groups.append((mask,aliases))
designs={};diagnostics=[]
for part,ff in parts.items():
    phase=np.array([r['phase'] for r in ff]);weight=np.array([r['weight'] for r in ff]);weight/=weight.sum()
    dd=[]
    for mask,aliases in groups:
        A=np.exp(-2j*np.pi*(phase@np.array(aliases).T))
        Aw=A*np.sqrt(weight[:,None]);inv=np.linalg.pinv(Aw)*np.sqrt(weight[None,:])
        dd.append(inv)
        diagnostics.append(dict(part=part,aliases=aliases,frames=len(ff),weighted_condition=float(np.linalg.cond(Aw)),coefficient_noise_amplification=[float(v) for v in np.sum(abs(inv)**2/weight[None,:],axis=1)]))
    designs[part]=dd
save('A4_joint_plan.json',dict(method=__doc__,frames=frames,designs=diagnostics,target='Full known seeing plus physical pixel image; unchanged A2 target and gates',band='Recover four aliases per native frequency, continuous native u/v frequencies [-1,1). This is a qualification grid, not a proposed new output FOV.',weights='Same frozen scalar variance weights as A2, no residual-based selection',gates='Every wavelength and all/early/late: baseline RMS <2G; injected texture gain .995..1.005 and relative RMS <.01',limitations=['Same synthetic scene across epochs; real solar scene changes','Exact registration, fixed seeing .97; neither asserted for captures','Noise amplification is measured; noiseless PASS alone does not qualify astronomical reconstruction','Finite reconstruction band may omit aliases, tested against the full fine-grid target']))
results=[];bases={}
for lam in WAVELENGTHS_NM:
    H=airy_otf(freq,lam)
    for wave in [None,8,16,32]:
        start=time.time();latent=baseline if wave is None else baseline+np.where(P,25*np.sin(2*np.pi*(X*np.cos(.37)+Y*np.sin(.37))/wave),0)
        Xt=rfftn(latent)*Hc*Hp;Yt=Xt*H
        observed={};truth={}
        for frame in frames:
            pu,pv=frame['phase'];ph=np.exp(-2j*np.pi*(fu*pu+fv*pv))
            truth[frame['stem']]=irfftn(Xt*ph,s=latent.shape)[::OVER,::OVER]
            yy=irfftn(Yt*ph,s=latent.shape)[::OVER,::OVER]
            observed[frame['stem']]=fft2(yy)/N**2*np.exp(2j*np.pi*(fu0*pu+fv0*pv))
        for part,ff in parts.items():
            obs=np.array([observed[r['stem']] for r in ff]);components=[]
            for (mask,aliases),inv in zip(groups,designs[part]):
                coeff=np.einsum('ai,ijk->ajk',inv,obs,optimize=True)
                for k,(au,av) in enumerate(aliases):
                    ffreq=np.hypot(fu0+au,fv0+av)/np.sqrt(2)
                    aa=airy_otf(ffreq,lam)
                    corrected=np.where(mask,coeff[k]/np.maximum(aa,1e-15),0)
                    components.append((au,av,corrected))
            sums={key:np.zeros(wx.shape) for key in ['truth','joint']};ws=0.
            for frame in ff:
                pu,pv=frame['phase'];spectrum=np.zeros((N,N),complex)
                for au,av,cc in components:spectrum+=cc*np.exp(-2j*np.pi*((fu0+au)*pu+(fv0+av)*pv))
                recovered=ifft2(spectrum*N**2).real
                coords=[N/2+pv+vw,N/2+pu+uw]
                for key,arr in [('truth',truth[frame['stem']]),('joint',recovered)]:
                    sums[key]+=frame['weight']*map_coordinates(arr,coords,order=1,mode='wrap',prefilter=False).reshape(wx.shape)
                ws+=frame['weight']
            maps={k:v/ws for k,v in sums.items()}
            if wave is None:
                bases[lam,part]=maps;e=(maps['joint']-maps['truth'])[test];rms=float(np.sqrt(np.mean(e*e)))
                row=dict(wavelength_nm=lam,part=part,scene='baseline',rms_G=rms,maximum_abs_G=float(np.max(abs(e))),PASS=bool(rms<2))
                if part=='all':np.savez_compressed(OUT/f'A4_baseline_maps_{int(lam)}.npz',**maps,world_radius=wr)
            else:
                base=bases[lam,part];expected=(maps['truth']-base['truth'])[test];actual=(maps['joint']-base['joint'])[test]
                gain=float(actual@expected/(expected@expected));relative=float(np.linalg.norm(actual-expected)/np.linalg.norm(expected))
                row=dict(wavelength_nm=lam,part=part,scene=f'texture{wave}',gain=gain,relative_RMS=relative,PASS=bool(.995<=gain<=1.005 and relative<.01))
            results.append(row)
        save('A4_joint_phase_reconstruction.json',dict(method=__doc__,tests=results,designs=diagnostics,no_real_source_or_PSB_change=True))
        print(lam,wave,round(time.time()-start,2),[r for r in results if r['wavelength_nm']==lam and r['scene']=='baseline'] if wave is None else '',flush=True)
print('DONE',sum(r['PASS'] for r in results),'/',len(results),flush=True)
