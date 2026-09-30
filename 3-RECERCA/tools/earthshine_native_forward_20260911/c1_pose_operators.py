"""Frozen spatially withheld pose/core experiment on eight uncensored shorts.
No photographic registration change. Both lunar and solar sources share the
same rigid coordinate change; relative solar motion comes from ephemeris only.
"""
from native_operator import *
from scipy.optimize import least_squares
from scipy.sparse import save_npz
import time

meta=json.loads((OUT/'B0_matrices.json').read_text())['frames']
profiles=json.loads((OUT/'C0_native_pose_profiles.json').read_text())['profiles']
audit=json.loads((OUT/'C0_native_pose_audit.json').read_text())
ref=audit['reference'];poses={a['stem']:np.array([a['dx'],a['dy']]) for a in audit['poses'] if a['status']=='DESCRIPTIVE_POSE'};poses[ref]=np.zeros(2)
stems=['572A2973','572A2974','572A2975','572A2976','572A2991','572A2992','572A2993','572A2994']
train=[s for s in stems if s not in ['572A2976','572A2994']]
pr=[a for a in profiles if a['stem']==ref and 30<=a['angle']<=330 and a['fit'] and a['fit']['qualified']]
ang=np.deg2rad([a['angle'] for a in pr]);A=np.stack([np.cos(ang),np.sin(ang)],1);b=np.array([a['fit']['center'] for a in pr]);err=np.array([max(.05,a['fit']['center_se_conditional']) for a in pr])
fit=least_squares(lambda d:(A@d-b)/err,[0,0],loss='soft_l1',f_scale=3);reference_pose=fit.x
sigmas={s:float(np.median([a['fit']['sigma_optical_descriptive'] for a in profiles if a['stem']==s and 30<=a['angle']<=330 and a['fit'] and a['fit']['qualified']])) for s in stems}
rows,_=source_rows();rows=[r for r in rows if r['stem'] in stems]
inventory=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())
native={r['stem']:r['native'] for r in inventory['frames']}
centers={r['stem']:np.array(r['solar_center_in_lunar_grid'])-np.array(native[r['stem']]['shift']) for r in rows}
reference=np.mean([centers[s] for s in train],axis=0)
frozen=[]
for r in rows:
    s=r['stem'];frozen.append(dict(stem=s,train=s in train,exp=r['exp'],time_C2=r['time_C2'],pose=(poses[s]+reference_pose).tolist(),sigma_outside_right=sigmas[s],solar_shift=(centers[s]-reference).tolist()))
plan=dict(method=__doc__,train=train,reserved=['572A2976','572A2994'],reference_pose=reference_pose.tolist(),reference_pose_fit_rms=float(np.sqrt(np.mean((A@fit.x-b)**2))),frames=frozen,variants=['baseline','pose','pose_core'],lambda_scaled=10,validation='Native right-hand observations identical in all variants; inspect reserved radial415-435,435-445,445-449,449-454,454-480. No source recovery PASS merely from lower residual.',limits=['Pose and core are descriptive fits outside the target sector, not uniquely measured physical PSF','Long exposures excluded from this experiment because an uncensored limb pose was not measured','Same historical global calibration and contour; spatial withholding is not full RAW independence'])
save('C1_pose_operator_plan.json',plan)
folder=OUT/'pose_matrices';folder.mkdir(exist_ok=False);geo=Geometry(16);qm=geo.quadrature(order=4);receipts=[]
for r in frozen:
    start=time.time();s=r['stem'];data=dict(np.load(OUT/'matrices'/f'{s}_observations.npz'));qc=geo.quadrature(r['solar_shift'],inside=False,order=4);variants={}
    for variant in plan['variants']:
        points=data['xy'] if variant=='baseline' else data['xy']-np.array(r['pose']);sigma=.97 if variant!='pose_core' else r['sigma_outside_right']
        M=response_matrix(points,data['J'],qm,sigma,radius=max(6.5,6*sigma+1));C=response_matrix(points,data['J'],qc,sigma,radius=max(6.5,6*sigma+1));error=float(np.max(abs(M@np.ones(geo.size)+C@np.ones(geo.size)-1)));assert error<1e-6,(s,variant,error)
        save_npz(folder/f'{s}_{variant}_lunar.npz',M);save_npz(folder/f'{s}_{variant}_solar.npz',C);variants[variant]=dict(sigma=sigma,constant_max_error=error)
    receipts.append(dict(**r,variants=variants,seconds=time.time()-start));save('C1_pose_operators.json',dict(frames=receipts,shape=geo.shape,plan='C1_pose_operator_plan.json'));print(s,json.dumps(variants),'seconds',round(time.time()-start,2),flush=True)
