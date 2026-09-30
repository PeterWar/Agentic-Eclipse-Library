"""Retrospective model-adequacy audit prompted by visual review, not a new fit.
The B0/B1 epoch reductions remain recorded but cannot identify the pupil when
the exterior linear-intensity model fails its own training observations.
"""
from diffraction_common import *
p=json.loads((OUT/'B0_native_profiles.json').read_text());d=np.array(p['distance']);rows=[]
for frame in p['frames']:
    for prof in frame['profiles']:
        g=np.array(prof['mean']);var=np.array(prof['variance']);valid=np.array(prof['valid']);deep=valid&(d<=-27);A=np.stack([np.ones_like(d),d/30],1);w=1/var[deep];normal=A[deep].T@(w[:,None]*A[deep]);cov=np.linalg.inv(normal);anchor=cov@(A[deep].T@(w*g[deep]))
        for name,fit in prof['fits'].items():
            coef=np.array(fit['coef']);slope_z=float((coef[1]-anchor[1])/np.sqrt(cov[1,1]));rows.append(dict(stem=frame['stem'],epoch=frame['epoch'],sector=prof['sector'],model=name,training_chi2=fit['training_chi2'],boundary=fit['boundary'],deep_only_moon_line=anchor.tolist(),global_moon_line=coef[:2].tolist(),deep_slope_discrepancy_sigma=slope_z,training_chi2_over5=bool(fit['training_chi2']>5),slope_discrepancy_over3sigma=bool(abs(slope_z)>3)))
summary={name:dict(fits=sum(r['model']==name for r in rows),training_chi2_over5=sum(r['model']==name and r['training_chi2_over5'] for r in rows),deep_slope_discrepancy_over3sigma=sum(r['model']==name and r['slope_discrepancy_over3sigma'] for r in rows),boundary=sum(r['model']==name and r['boundary'] for r in rows)) for name in ['gaussian','airy550']}
save('B2_profile_adequacy_audit.json',dict(method=__doc__,summary=summary,rows=rows,threshold_status='Retrospective diagnostic flags chi2>5 and deep-only slope discrepancy>3conditional sigma; not predeclared validation gates or calibrated probabilities',finding='Some exterior profiles have a strong limb peak followed by rapid decay; a linear exterior radiance cannot reproduce them. Global fit compensates with an unsupported lunar slope.',decision='B0/B1 numerical reductions are not accepted as physical evidence for pupil identification or lunar recovery. Do not subtract these profiles, apply their geometry or promote their seeing values.',limits='Conditional variance and radial bins share calibration; slope flags are descriptive. No new model selected on heldout data.',no_source_or_PSB_change=True))
print('ADEQUACY',summary,flush=True)
