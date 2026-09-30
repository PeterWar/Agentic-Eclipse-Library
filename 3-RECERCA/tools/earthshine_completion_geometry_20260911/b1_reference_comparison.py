"""Predict held-out native lunar phases from independently measured solar shifts.
One common angular phase is estimated on calibration frames only. No target
Moon pixel or per-target adjustment selects a predicted phase.
"""
from geometry_common import *
from scipy.optimize import least_squares
solar={r['stem']:r for r in json.loads((OUT/'A1_solar_registration.json').read_text())['frames']}
profiles=json.loads((OUT/'B0_lunar_profiles.json').read_text())['profiles']
def normal(angle):return np.array([np.cos(np.deg2rad(angle)),np.sin(np.deg2rad(angle))])
usable=[r for r in profiles if r['fit'] and r['fit']['qualified']]
reference=[]
for angle in np.arange(0.,360.,15.):
    rows=[r for r in usable if r['stem'] in CAL and r['angle']==angle and solar[r['stem']]['eligible']]
    if len(rows)<6:continue
    delta=np.array([r['fit']['center']-normal(angle)@solar[r['stem']]['fits'][0]['parameters'][:2] for r in rows]);err=np.array([max(.05,r['fit']['center_se_conditional']) for r in rows]);opt=least_squares(lambda p:(p[0]-delta)/err,[np.median(delta)],loss='soft_l1',f_scale=3)
    reference.append(dict(angle=float(angle),common_phase=float(opt.x[0]),calibration_frames=[r['stem'] for r in rows],calibration_rms=float(np.sqrt(np.mean((delta-opt.x[0])**2))),sigma_descriptive_median=float(np.median([r['fit']['sigma_descriptive'] for r in rows]))))
ref={r['angle']:r for r in reference};results=[]
for stem in CAL+TEST:
    sol=solar[stem];rows=[r for r in usable if r['stem']==stem and r['angle'] in ref];pairs=[]
    for r in rows:
        n=normal(r['angle']);prediction=ref[r['angle']]['common_phase']+n@sol['fits'][0]['parameters'][:2]
        pairs.append(dict(angle=r['angle'],measured=r['fit']['center'],prediction=float(prediction),residual=float(r['fit']['center']-prediction),se=r['fit']['center_se_conditional']))
    fits=[]
    for part in ['all',0,1]:
        use=[r for r in pairs if part=='all' or int(r['angle']/15)%2==part]
        if len(use)<4:fits.append(None);continue
        A=np.array([normal(r['angle']) for r in use]);b=np.array([r['residual'] for r in use]);err=np.maximum(.05,[r['se'] for r in use]);opt=least_squares(lambda p:(A@p-b)/err,np.zeros(2),loss='soft_l1',f_scale=3)
        fits.append(dict(delta=opt.x.tolist(),rms_after=float(np.sqrt(np.mean((b-A@opt.x)**2))),sectors=len(use)))
    gap=float(np.linalg.norm(np.array(fits[1]['delta'])-fits[2]['delta'])) if all(fits) else None;rms=float(np.sqrt(np.mean([r['residual']**2 for r in pairs]))) if pairs else None;passed=bool(sol['eligible'] and len(pairs)>=8 and rms<=.25 and gap is not None and gap<=.30)
    results.append(dict(stem=stem,heldout=stem in TEST,solar_eligible=sol['eligible'],sectors=len(pairs),predicted_phase_rms=rms,descriptive_remaining_rigid_pose=fits,angular_half_pose_gap=gap,PASS=passed,pairs=pairs));print(stem,'n',len(pairs),'rms',round(rms,3) if rms else rms,'residual pose',fits[0],'PASS',passed)
save('B1_reference_comparison.json',dict(method=__doc__,common_angular_phase=reference,frames=results,heldout_PASS=all(r['PASS'] for r in results if r['heldout']),limits=['Solar shifts use a target-excluded short reference but are fitted independently to each target outer corona','Common angular phase is empirical; not a newly measured topographic lunar contour','Residual poses are diagnostics only, not used in predictions or images','Short-frame conditional errors share calibration and original coordinate metadata']))
