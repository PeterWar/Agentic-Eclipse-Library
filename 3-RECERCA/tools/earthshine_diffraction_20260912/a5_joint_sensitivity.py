"""Stress A4 with fixed registration errors and changing seeing/solar light.
These are declared sensitivity scenarios, not measurements of the captures.
The target remains the fully sampled seeing+pixel truth for each frame.
"""
from diffraction_common import *
original=(HERE/'a4_joint_phase_reconstruction.py').read_text()
cases=[('exact',0.,0.,0.),('phase01',.01,0.,0.),('phase05',.05,0.,0.),('seeing05',0.,.05,0.),('solar01',0.,0.,.01)]
summaries=[]
save('A5_sensitivity_plan.json',dict(method=__doc__,cases=cases,phase_error_unit='Native u/v pixel, fixed sine/cosine sequence from immutable input ordering; each axis RMS equal to declared value',seeing='True sigma varies sinusoidally with declared RMS; estimator still assumes a common scene',solar='Only the local synthetic prominence varies in brightness by declared RMS fraction; Moon and uniform background constant',gates='Unchanged <2G baseline RMS; sensitivity FAIL does not negate the exact-scene numerical PASS',scope='No real registration/seeing estimate; no source or PSB change'))
for tag,jitter,seeing,solar in cases:
    code=original.replace('A4_',f'A5_{tag}_').replace('for lam in WAVELENGTHS_NM:','for lam in [550.]:').replace('for wave in [None,8,16,32]:','for wave in [None]:')
    needle="pu,pv=frame['phase'];ph=np.exp(-2j*np.pi*(fu*pu+fv*pv))"
    new="""pu,pv=frame['phase'];ii=frames.index(frame);zz=2*np.pi*ii/len(frames)
            du=SENS_JITTER*np.sqrt(2)*np.sin(zz);dv=SENS_JITTER*np.sqrt(2)*np.cos(zz)
            sig=.97+SENS_SEEING*np.sqrt(2)*np.sin(zz)
            scene=latent+np.where(P,0,70000*np.exp(-((X-124)**2+(Y-9)**2)/(2*8**2))*SENS_SOLAR*np.sqrt(2)*np.sin(zz))
            Xt_frame=rfftn(scene)*np.exp(-2*np.pi**2*sig**2*freq**2)*Hp
            Yt_frame=Xt_frame*H
            ph=np.exp(-2j*np.pi*(fu*(pu+du)+fv*(pv+dv)))"""
    assert needle in code
    code=code.replace(needle,new).replace('irfftn(Xt*ph,','irfftn(Xt_frame*ph,').replace('irfftn(Yt*ph,','irfftn(Yt_frame*ph,')
    env=dict(__builtins__=__builtins__,SENS_JITTER=jitter,SENS_SEEING=seeing,SENS_SOLAR=solar)
    exec(compile(code,str(HERE/'a4_joint_phase_reconstruction.py')+' [sensitivity '+tag+']','exec'),env)
    data=json.loads((OUT/f'A5_{tag}_joint_phase_reconstruction.json').read_text())
    summaries.append(dict(case=tag,jitter_rms=jitter,seeing_rms=seeing,solar_fraction_rms=solar,tests=data['tests']))
    save('A5_joint_sensitivity.json',dict(method=__doc__,cases=summaries,no_real_source_change=True))
print('SENSITIVITY DONE',flush=True)
