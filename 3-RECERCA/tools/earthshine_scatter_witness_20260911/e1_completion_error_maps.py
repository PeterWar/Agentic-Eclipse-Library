"""Localize the failed completion without fitting any new parameter."""
from scatter_common import *
import ast,cv2
from scipy.ndimage import gaussian_filter
src=np.load(OUT/'D2_auxiliary_corona.npz');Ce=src['solar'];validc=src['valid'];moon=float(src['moon_level']);frames={r['stem']:r for r in json.loads((OUT/'D2_training_sources.json').read_text())['frames']};yy,xx=np.mgrid[:N,:N].astype(np.float32);rad=np.hypot(xx-CX,yy-CY);distance=np.load(OUT/'D2_training_sources.npz')['source_lunar_distance'];P=np.clip(.5-distance,0,1);p=json.loads((OUT/'B1_physical_mixture.json').read_text())['p'];a=p/(1-p);coeff=np.array([a,-a*a,a**3,-a**4])
for path,name in [(HERE/'d2_refined_completion.py','auxiliary'),(HERE/'completion.py','broad_correction')]:
    fn=next(r for r in ast.parse(path.read_text()).body if isinstance(r,ast.FunctionDef) and r.name==name);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec'))
mask_source=np.load(SRC/'A0_quincunx_572A2983.npz');mask=np.isfinite(mask_source['g'])&(mask_source['q']>0);angle=np.arctan2(yy-CY,xx-CX)%(2*np.pi);results=[]
for stem in ['572A2967','572A3003']:
    z=np.load(SRC/f'A0_quincunx_{stem}.npz');g=z['g'];valid=np.isfinite(g)&(z['q']>0);truth,mass=broad_correction(g,valid);model,mgood=auxiliary(stem);kept=valid&mask;fill=(~kept)&mgood;completed=np.where(kept,g,np.where(fill,model,0));estimate,support=broad_correction(completed,kept|fill);qualified=valid&(mass>=.995)&(support>=.995);error=estimate-truth;sectors=[]
    for k in range(24):
        use=qualified&(rad>=435)&(rad<449)&(np.floor(angle/(np.pi/12)).astype(int)==k)
        if use.any():sectors.append(dict(angle_center_deg=15*k+7.5,pixels=int(use.sum()),median_signed_G=float(np.median(error[use])),median_abs_G=float(np.median(abs(error[use]))),p95_abs_G=float(np.percentile(abs(error[use]),95))))
    np.savez_compressed(OUT/f'E1_completion_map_{stem}.npz',truth_broad_correction=truth.astype(np.float32),predicted_broad_correction=estimate.astype(np.float32),correction_error=error.astype(np.float32),qualified=qualified,remaining_actual_mask=kept,auxiliary_observed_field=model.astype(np.float32),observed_short=g)
    row=dict(stem=stem,mask_RAW='572A2983',sectors=sectors);results.append(row);print(stem,'worst sectors',sorted(sectors,key=lambda r:-r['p95_abs_G'])[:3],flush=True)
save('E1_completion_error_maps.json',dict(method=__doc__,frames=results,parameter_fitting=False))
