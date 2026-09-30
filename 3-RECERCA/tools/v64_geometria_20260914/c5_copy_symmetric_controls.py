from pathlib import Path
import json,numpy as np,cv2
from scipy.optimize import minimize
p=Path('research/tools/v64_geometria_20260914/c4_copy_symmetric.py');s=p.read_text();exec(compile(s.split('opt=solve(b);')[0],str(p),'exec'))
rep=[]
for truth in [[0,0,0,1],[1.25,-.75,.17,1]]:
    ma=matrix(truth);ma[:,2]+=ma[:,:2]@np.array([4377,2777])-np.array([4377,2777]);field=cv2.warpAffine(globals()['s'],ma,(2000,2000),flags=cv2.INTER_CUBIC);sol=solve(field);err=sol.x-np.array(truth);bound=float(np.linalg.norm(err[:2])+650*(abs(np.deg2rad(err[2]))+abs(err[3])))
    rep.append(dict(injected=truth,recovered=sol.x.tolist(),max_displacement_bound_px=bound,reserved_ncc=score(sol.x,field,~fit),PASS=bound<.15))
real=json.loads((O/'C4_copy_symmetric_registration.json').read_text());q=np.array(real['sampling_transform_source_to_extra']);local=[]
for k in range(12):
    sel=sector==k
    if sel.sum()<80:continue
    def sc(d):z=q.copy();z[:2]+=d;return score(z,sel=sel)
    opt=minimize(lambda d:-sc(d),[0,0],method='Nelder-Mead',bounds=[(-1,1),(-1,1)],options={'xatol':1e-5});local.append(dict(sector=k,reserved=bool(k%2),residual_dxdy=opt.x.tolist(),residual_px=float(np.linalg.norm(opt.x)),ncc=-float(opt.fun)))
out=dict(controls=rep,local_after_real_registration=local,rotated180_null=score([0,0,180,1]),PASS=all(x['PASS'] for x in rep) and max(x['residual_px'] for x in local)<.3)
(O/'C5_copy_symmetric_controls.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
