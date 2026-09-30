"""Build the declared12 native data operators, moving and static solar controls.
Training/reserved partition and initial sigma were declared before fitting.
"""
from native_operator import *
from scipy.sparse import save_npz
import time
assert json.loads((OUT/'A0_operator_pilot.json').read_text())['PASS']
geo=Geometry(PLAN['limb_polygon_refinement']);rows,reference=source_rows();qm=geo.quadrature(order=4);qstatic=geo.quadrature(inside=False,order=4);out=OUT/'matrices';out.mkdir(exist_ok=False);receipts=[]
for m in rows:
    start=time.time();data=observed(m);qc=geo.quadrature(m['solar_shift'],inside=False,order=4);points=data['xy'];J=data['J'];sigma=PLAN['gaussian_optical_sigma_assumed']
    matrices={'lunar':response_matrix(points,J,qm,sigma),'solar_moving':response_matrix(points,J,qc,sigma),'solar_static':response_matrix(points,J,qstatic,sigma)}
    one=np.ones(geo.size);checks={key:float(np.max(abs(matrices['lunar']@one+matrices[key]@one-1))) for key in ['solar_moving','solar_static']};assert max(checks.values())<1e-6,checks
    for key,a in matrices.items():save_npz(out/f'{m["stem"]}_{key}.npz',a)
    np.savez_compressed(out/f'{m["stem"]}_observations.npz',**data)
    r=dict(stem=m['stem'],exp=m['exp'],time_C2=m['time_C2'],train=m['train'],solar_shift=m['solar_shift'].tolist(),samples=len(points),native_gaussian_sigma_assumed=sigma,constant_max_error=checks,nnz={k:a.nnz for k,a in matrices.items()},seconds=time.time()-start);receipts.append(r);save('B0_matrices.json',dict(method=__doc__,frames=receipts,solar_reference=reference.tolist(),shape=geo.shape,scene_box=geo.box,weight_variance='Native green-lattice Gaussian sigma4px, weights only; observed radiance not smoothed',status='Operators built; real-scene fit and independent predictions pending'))
    print(m['stem'],r['samples'],'DONE',round(r['seconds'],2),flush=True)
print('DONE12',flush=True)
