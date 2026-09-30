"""Native sampling qualification of independently specified pupil diffraction.
Periodic fine-grid phantom makes the boundary condition explicit and shared.
It is numerical validation only, never an astronomical source image.
"""
from diffraction_common import *
from scipy.fft import rfftn,irfftn,fftfreq,rfftfreq
import time
N=256;OVER=8;FINE=N*OVER;step=1/OVER;uv=np.arange(FINE)*step;V,U=np.meshgrid(uv,uv,indexing='ij');fv=fftfreq(FINE,d=step)[:,None];fu=rfftfreq(FINE,d=step)[None,:];freq=np.sqrt(fu*fu+fv*fv)/np.sqrt(2);Hcore=np.exp(-2*np.pi**2*.97**2*freq**2);Hpix=np.sinc((fu+fv)/2)*np.sinc((fu-fv)/2);Hband=np.exp(-2*np.pi**2*2**2*freq**2);fv0=fftfreq(N)[:,None];fu0=rfftfreq(N)[None,:];freq0=np.sqrt(fu0*fu0+fv0*fv0)/np.sqrt(2);band0=np.exp(-2*np.pi**2*2**2*freq0**2)
save('A1_native_plan.json',dict(method=__doc__,native_lattice_side=N,oversampling=OVER,seeing_sigma=.97,aperture='Exact square-pixel sinc transfer in raw x/y coordinates before sampling native u/v lattice',pupil='No free parameters;90mm aperture and measured angular scale, spectral bracket500/550/600',scene='Known periodic dark disk R120px on uniform solar background, local synthetic prominence and lunar sinusoidal injections; no real terrain simulated or used as a source',phases=['572A2976','572A2994'],full_inverse='1/AiryOTF on native sampled lattice; target is known seeing+pixel integrated image',regularized_inverse='1+G2*(1/AiryOTF-1), predeclared sigma2px; target is Y+G2*(X-Y), not full seeing-onlyX',gates='Perphase/wavelength baselineRMS<2G at1-20px inside known disk; all signals gain0.995..1.005 and relativeRMS<.01. Check native aliasing before any real-image correction.',boundary='All transforms share the same periodic fine-grid scene. No claim of finite real-image boundary completeness.'))
results=[]
for stem in ['572A2976','572A2994']:
    z=np.load(NATIVE/f'D0_native_field_{stem}.npz');J=z['native_to_world'];nmoon=(np.array([CX,CY])-z['world_origin'])@np.linalg.inv(J).T;phase=np.array([(nmoon[0]+nmoon[1]-1)/2,(nmoon[0]-nmoon[1]-1)/2])%1;du=U-(N/2+phase[0]);dv=V-(N/2+phase[1]);nx=du+dv;ny=du-dv;X=J[0,0]*nx+J[0,1]*ny;Y=J[1,0]*nx+J[1,1]*ny;rad=np.hypot(X,Y);P=rad<120;solar=100000+70000*np.exp(-((X-124)**2+(Y-9)**2)/(2*8**2));baseline=np.where(P,650,solar);test=(rad[::OVER,::OVER]>=100)&(rad[::OVER,::OVER]<119)
    for lam in WAVELENGTHS_NM:
        H=airy_otf(freq,lam);H0=airy_otf(freq0,lam);assert H0.min()>.5;bases={}
        for wave in [None,8,16,32]:
            start=time.time();latent=baseline if wave is None else baseline+np.where(P,25*np.sin(2*np.pi*(X*np.cos(.37)+Y*np.sin(.37))/wave),0);F=rfftn(latent);Xf=F*Hcore*Hpix;Yf=Xf*H;observed=irfftn(Yf,s=latent.shape)[::OVER,::OVER];xf=irfftn(Xf,s=latent.shape)[::OVER,::OVER];bf=irfftn(Yf+Hband*(Xf-Yf),s=latent.shape)[::OVER,::OVER];Y0=rfftn(observed);rec_full=irfftn(Y0/H0,s=observed.shape);rec_band=irfftn(Y0*(1+band0*(1/H0-1)),s=observed.shape)
            for name,recovered,truth in [('full',rec_full,xf),('regularized_sigma2',rec_band,bf)]:
                if wave is None:
                    bases[name]=(recovered.copy(),truth.copy());err=(recovered-truth)[test];rms=float(np.sqrt(np.mean(err**2)));row=dict(stem=stem,wavelength_nm=lam,operator=name,scene='baseline',samples=int(test.sum()),rms_G=rms,max_abs_G=float(np.max(abs(err))),PASS=bool(rms<2))
                else:
                    expected=(truth-bases[name][1])[test];actual=(recovered-bases[name][0])[test];gain=float(actual@expected/(expected@expected));relative=float(np.linalg.norm(actual-expected)/np.linalg.norm(expected));row=dict(stem=stem,wavelength_nm=lam,operator=name,scene=f'texture{wave}',samples=int(test.sum()),gain=gain,relative_RMS=relative,PASS=bool(.995<=gain<=1.005 and relative<.01))
                results.append(row)
            save('A1_native_inverse_check.json',dict(method=__doc__,tests=results,scope='Discrete fine-grid periodic-scene numerical qualification only; no real-frame completion or optical-PSF identification'))
        print(stem,lam,[(r['operator'],round(r['rms_G'],5),r['PASS']) for r in results if r['stem']==stem and r['wavelength_nm']==lam and r['scene']=='baseline'],flush=True)
print('DONE',len(results),flush=True)
