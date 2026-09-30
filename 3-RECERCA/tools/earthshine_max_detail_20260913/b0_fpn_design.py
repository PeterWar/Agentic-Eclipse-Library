"""Freeze and quantify Fourier self-calibration conditioning from actual poses."""
from common import *
claim();j=json.loads((OUT/'A2_detector_diversity.json').read_text());poses=j['poses'];centres=np.array(j['centres']);A=np.array(poses[0]['roi_to_native'])[:,:2];shifts=(np.linalg.inv(A)@(centres-centres[0]).T).T
angles=np.arange(360)*np.pi/180;fr=json.loads((OUT/'A0_freeze.json').read_text())['pilot_frames'];v=[m for m in fr if m['tren']=='vixen'];names=[p['stem'] for p in poses]
ex=np.array([p['exp'] for p in poses]);weights=ex/np.where(ex>=10,35.54865158,np.where(ex>=2,32.94040478,14.82631372));weights/=weights.sum();rows=[]
for wavelength in [8,16,24,40,64,96]:
    phase=np.exp(2j*np.pi/wavelength*(shifts[:,0,None]*np.cos(angles)+shifts[:,1,None]*np.sin(angles)));rho=np.abs(np.sum(weights[:,None]*phase,axis=0));inflation=1/np.maximum(1-rho**2,1e-12)
    rows.append(dict(wavelength=wavelength,variance_inflation_p=[float(np.percentile(inflation,q)) for q in [0,25,50,75,95,100]],fraction_inflation_le4=float(np.mean(inflation<=4))))
save('B0_fpn_design.json',dict(method=__doc__,names=names,shifts_common=shifts,weights=weights,rows=rows,
    pilot=dict(box=[444,444,956,956],size=512,window='Tukey alpha0.5 after per-frame total-degree3 polynomial removed',models=['fixed calibrated detector pattern','raw DN offset pattern scaled inverse exposure','both patterns'],ridge=[.1,1.,10.],fit='A0 training frames only; select by leave-one-training-frame-out weighted residual16-64',reserved='A0 test frames: no model changes after viewing',null='Permute detector poses among source frames with seed551310; same fit/holdout machinery',injection_seed=551309,outputs='Source pilot only. Windowed spectral model approximate near patch edges; no output to Photoshop.'),
    limits=['Almost one-dimensional drift leaves perpendicular Fourier modes poorly identifiable','Solar scatter, PSF and temporal offsets may violate stationary lunar scene','Cross-sensor check and planted-detector/scene controls required before promotion']))
print('DITHER',rows,flush=True)
