"""Profile registration cycles and agreement with fully observed optical edges."""
import b0_censored_profile_registration as b
from b0_censored_profile_registration import *
links={}
for a,c in [(2976,2977),(2977,2978),(2976,2978),(2978,2976)]:
    b.ref=z[f'g{a}'].astype(float);b.refvalid=z[f'valid{a}']
    f=solve(z[f'g{c}'],z[f'valid{c}'],np.ones(len(th),bool),2)
    links[f'{a}_{c}']=f;print(a,c,f,flush=True)
p=lambda a,c:np.array(links[f'{a}_{c}']['parameters'])
cycle=float(np.linalg.norm(p(2976,2977)+p(2977,2978)-p(2976,2978)))
reverse=float(np.linalg.norm(p(2976,2978)+p(2978,2976)))
opt=json.loads((ROOT/'output/earthshine_compatibility_20260911/C1_lunar_geometry.json').read_text())['rows'];opt={x['frame']:x for x in opt}
wing=json.loads((OUT/'B0_profile_registration.json').read_text())['frames'];checks={}
for n in [2988,2994]:
    actual=np.array([opt[n]['fit'][c]-opt[2976]['fit'][c] for c in ['dx','dy']]);estimated=np.array(wing[str(n)]['2']['fits'][0]['parameters']);checks[n]=dict(optical_difference=actual.tolist(),wing_difference=estimated.tolist(),gap=float(np.linalg.norm(actual-estimated)))
rep=dict(links=links,cycle_gap_pixels=cycle,reverse_gap_pixels=reverse,optical_checks=checks,pass_geometry=bool(cycle<.5 and reverse<.5 and all(v['gap']<.5 for v in checks.values())),limits='Internal geometric corroboration, not independent other-telescope texture validation or proof of PSF equality. Radius not changed.')
(OUT/'B1_geometry_checks.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep),flush=True)
sh=json.loads((ROOT/'output/earthshine_compatibility_20260911/B1_relative_geometry.json').read_text())['source_shifts']
for n in ['2977','2978']:
    sh[n]=(np.array(sh[n])-wing[n]['2']['fits'][0]['parameters']).tolist()
(OUT/'B1_candidate_shifts.json').write_text(json.dumps(dict(source_shifts=sh,formula='new_output_translation = previous_coronal_translation - residual_observed_lunar_translation',radius_correction=0),indent=2))
