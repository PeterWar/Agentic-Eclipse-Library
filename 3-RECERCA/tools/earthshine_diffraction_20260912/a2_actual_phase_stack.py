"""Test whether actual phase diversity removes single-frame inverse alias error.
Restore the full seeing+pixel target, including for the regularized comparison.
All data are known periodic phantoms; this is not a real-image completion test.
"""
from diffraction_common import *
from scipy.fft import rfftn,irfftn,fftfreq,rfftfreq
from scipy.ndimage import map_coordinates
import time
N=256;OVER=8;FINE=N*OVER;uv=np.arange(FINE)/OVER;V,U=np.meshgrid(uv,uv,indexing='ij');fv=fftfreq(FINE,d=1/OVER)[:,None];fu=rfftfreq(FINE,d=1/OVER)[None,:];freq=np.sqrt(fu*fu+fv*fv)/np.sqrt(2);Hc=np.exp(-2*np.pi**2*.97**2*freq**2);Hp=np.sinc((fu+fv)/2)*np.sinc((fu-fv)/2);f0=np.hypot(fftfreq(N)[:,None],rfftfreq(N)[None,:])/np.sqrt(2);band0=np.exp(-2*np.pi**2*4*f0*f0);records=json.loads((NATIVE/'D0_native_fields.json').read_text())['frames'];epochs={r['stem']:r for r in json.loads((NATIVE/'D1_inputs.json').read_text())['frames']};frames=[]
for row in records:
    z=np.load(row['file']);valid=z['valid']&(z['q']>0)&np.isfinite(z['g'])
    if not valid.all():continue
    native=np.load(SRC/f'A0_native_samples_{row["stem"]}.npz');r=np.hypot(native['x']-CX,native['y']-CY);use=(r>=415)&(r<435)&native['valid'];weight=1/float(np.median(native['variance'][use]));J=z['native_to_world'];nmoon=(np.array([CX,CY])-z['world_origin'])@np.linalg.inv(J).T;phase=np.array([(nmoon[0]+nmoon[1]-1)/2,(nmoon[0]-nmoon[1]-1)/2])%1;frames.append(dict(stem=row['stem'],phase=phase.tolist(),weight=weight,epoch=epochs[row['stem']]['epoch'],half='early' if epochs[row['stem']]['time_C2']<60 else 'late',J=J.tolist()))
assert len(frames)==21
save('A2_stack_plan.json',dict(method=__doc__,frames=frames,selection='All21D0fields with no censored/invalid pixel; selection by validity only',weights='Frozen native variance median at415-435; not selected from phantom residuals',transforms='Exactly registered physical scene, actual fractional green phases, same positive bilinear output interpolation for observed/true/corrected data',gates='Full weighted stack and early/late halves: baseline RMS<2G in1-20px inside edge, texture gain0.995..1.005 and relativeRMS<.01. Per-frame failures remain reported; a stack gate has different scope.',target='Full known seeing+pixel image for every operator; no substitution of a regularized easier target',limitations=['Synthetic exact registration, fixed seeing0.97 and same scene across time; does not prove real alignment or temporal coronal completion','Periodic numerical boundary, not real sky outside captured field','No astronomical texture or image source created']))
J=np.array(frames[0]['J']);du=U-N/2;dv=V-N/2;rawx=du+dv;rawy=du-dv;X=J[0,0]*rawx+J[0,1]*rawy;Y=J[1,0]*rawx+J[1,1]*rawy;rad=np.hypot(X,Y);P=rad<120;baseline=np.where(P,650,100000+70000*np.exp(-((X-124)**2+(Y-9)**2)/(2*8**2)));wy,wx=np.mgrid[-140:141,-140:141].astype(float);wr=np.hypot(wx,wy);test=(wr>=100)&(wr<119);world=np.stack([wx.ravel(),wy.ravel()],1);nxy=world@np.linalg.inv(J).T;uw=(nxy[:,0]+nxy[:,1])/2;vw=(nxy[:,0]-nxy[:,1])/2;results=[];baseline_maps={};frame_results=[]
for lam in WAVELENGTHS_NM:
    H=airy_otf(freq,lam);H0=airy_otf(f0,lam);filters={'observed':np.ones_like(H0),'full':1/H0,'regularized_sigma2':1+band0*(1/H0-1)}
    for wave in [None,8,16,32]:
        start=time.time();latent=baseline if wave is None else baseline+np.where(P,25*np.sin(2*np.pi*(X*np.cos(.37)+Y*np.sin(.37))/wave),0);F=rfftn(latent);Xt=F*Hc*Hp;Yt=Xt*H;sums={part:{key:np.zeros(wx.shape) for key in ['truth']+list(filters)} for part in ['all','early','late']};weights={part:0. for part in sums}
        for frame in frames:
            pu,pv=frame['phase'];phase=np.exp(-2j*np.pi*(fu*pu+fv*pv));truth=irfftn(Xt*phase,s=latent.shape)[::OVER,::OVER];observed=irfftn(Yt*phase,s=latent.shape)[::OVER,::OVER];fy=N/2+pv+vw;fx=N/2+pu+uw;maps={'truth':map_coordinates(truth,[fy,fx],order=1,mode='wrap',prefilter=False).reshape(wx.shape)};obsfft=rfftn(observed)
            for name,filt in filters.items():
                corrected=observed if name=='observed' else irfftn(obsfft*filt,s=observed.shape);maps[name]=map_coordinates(corrected,[fy,fx],order=1,mode='wrap',prefilter=False).reshape(wx.shape)
            if wave is None:frame_results.append(dict(stem=frame['stem'],wavelength_nm=lam,rms_G={k:float(np.sqrt(np.mean((maps[k][test]-maps['truth'][test])**2))) for k in filters}))
            for part in ['all',frame['half']]:
                weights[part]+=frame['weight']
                for key in maps:sums[part][key]+=frame['weight']*maps[key]
        for part in sums:
            maps={k:v/weights[part] for k,v in sums[part].items()}
            if wave is None:
                baseline_maps[lam,part]=maps
                if part=='all':np.savez_compressed(OUT/f'A2_baseline_maps_{int(lam)}.npz',**maps,world_radius=wr)
            for name in filters:
                if wave is None:
                    error=maps[name]-maps['truth'];e=error[test];rms=float(np.sqrt(np.mean(e*e)));rows=[]
                    for d0,d1 in [(1,3),(3,6),(6,12),(12,20)]:
                        use=(wr>=120-d1)&(wr<120-d0);rows.append(dict(inside_distance=[d0,d1],median_signed_G=float(np.median(error[use])),min_G=float(np.min(error[use])),max_G=float(np.max(error[use]))))
                    row=dict(wavelength_nm=lam,part=part,operator=name,scene='baseline',rms_G=rms,maximum_abs_G=float(np.max(abs(e))),annuli=rows,PASS=bool(rms<2))
                else:
                    base=baseline_maps[lam,part];expected=(maps['truth']-base['truth'])[test];actual=(maps[name]-base[name])[test];gain=float(actual@expected/(expected@expected));relative=float(np.linalg.norm(actual-expected)/np.linalg.norm(expected));row=dict(wavelength_nm=lam,part=part,operator=name,scene=f'texture{wave}',gain=gain,relative_RMS=relative,PASS=bool(.995<=gain<=1.005 and relative<.01))
                results.append(row)
        save('A2_actual_phase_stack.json',dict(method=__doc__,tests=results,per_frame_baseline=frame_results,frames=frames,target='Full seeing+pixel image, including for regularized comparison',no_source_or_PSB_change=True));print(lam,wave,round(time.time()-start,2),'seconds',[(r['part'],r['operator'],round(r['rms_G'],4),r['PASS']) for r in results if r['wavelength_nm']==lam and r['scene']=='baseline'] if wave is None else '',flush=True)
print('DONE',len(results),flush=True)
