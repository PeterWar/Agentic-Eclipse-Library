"""Spatially withheld completion test of measured solar/lunar geometry.
Only auxiliary light predictions change. The score uses435-449px samples that
were excluded from both the native lunar-phase and outer-corona measurements.
No completed value enters a delivered eclipse image.
"""
from geometry_common import *
from scipy.ndimage import gaussian_filter,map_coordinates
import ast,time
src=np.load(PREV/'D2_auxiliary_corona.npz');Ce=src['solar'];validc=src['valid'];moon=float(src['moon_level']);frames={r['stem']:r for r in json.loads((PREV/'D2_training_sources.json').read_text())['frames']};yy,xx=np.mgrid[:N,:N].astype(np.float32);rad=np.hypot(xx-CX,yy-CY);angle=np.arctan2(yy-CY,xx-CX)%(2*np.pi);distance=np.load(PREV/'D2_training_sources.npz')['source_lunar_distance'];solar={r['stem']:r for r in json.loads((OUT/'A1_solar_registration.json').read_text())['frames']};phase=json.loads((OUT/'B1_reference_comparison.json').read_text());phase_rows={r['stem']:r for r in phase['frames']};profiles=json.loads((OUT/'B0_lunar_profiles.json').read_text())['profiles'];ref=phase['common_angular_phase'];ref_angle=np.deg2rad([r['angle'] for r in ref]);ref_value=[r['common_phase'] for r in ref];p=P_WIDE;a=p/(1-p);coeff=np.array([a,-a*a,a**3,-a**4]);fn=next(r for r in ast.parse((ROOT/'research/tools/earthshine_scatter_witness_20260911/completion.py').read_text()).body if isinstance(r,ast.FunctionDef) and r.name=='broad_correction');exec(compile(ast.Module(body=[fn],type_ignores=[]),'frozen_broad_correction','exec'))
variants=['baseline','solar_only','measured_lunar_phase','measured_phase_width']
save('C0_plan.json',dict(method=__doc__,variants=variants,targets=TEST,masks=LONG,phase_measurement='Common angular phase from12calibration RAWs, plus two rigid coordinates per target fitted to native r>=450 only. No435-449 target pixels select any parameter.',width='Per-target median of qualified native profile sigma; descriptive. No additional resampling term assumed.',solar='Per-target measured outer-corona translation and gain; offset applied outside Moon only. Unqualified solar fits remain labelled and cannot promote any variant.',gates='Each target/mask/radius medianabs<=5G,p95abs<=25G,support>=.80; no change to previous limits',scope='This is spatial withholding within each target exposure, not target-excluded RAW validation. It can diagnose the completion failure but cannot qualify censored long targets whose geometry is unavailable.'))
def sample(im,x,y):return map_coordinates(im,[y,x],order=1,mode='constant',cval=0,prefilter=False)
def auxiliary(stem,variant):
    sp=np.array(solar[stem]['fits'][0]['parameters']);delta=np.zeros(2) if variant=='baseline' else sp[:2];center=np.array(frames[stem]['solar_center']);sx=xx-(center[0]-CX)-delta[0];sy=yy-(center[1]-CY)-delta[1];C=sample(Ce,sx,sy);good=sample(validc.astype(float),sx,sy)>=1-1e-6
    if variant!='baseline':C=sp[2]*C+sp[3]
    dist=distance.copy();sigma=.97
    if variant in ['measured_lunar_phase','measured_phase_width']:
        residual=np.array(phase_rows[stem]['descriptive_remaining_rigid_pose'][0]['delta']);d=sp[:2]+residual;shift=np.interp(angle,ref_angle,ref_value,period=2*np.pi)+d[0]*np.cos(angle)+d[1]*np.sin(angle);dist=dist-shift
    if variant=='measured_phase_width':sigma=float(np.median([r['fit']['sigma_descriptive'] for r in profiles if r['stem']==stem and r['fit'] and r['fit']['qualified']]))
    P=np.clip(.5-dist,0,1);cover=P+(1-P)*good;F=P*moon+(1-P)*C*good;dc=gaussian_filter(cover,sigma,truncate=5);core=gaussian_filter(F,sigma,truncate=5)/np.maximum(dc,1e-30);db=gaussian_filter(dc,12,truncate=5);wide=gaussian_filter(core*dc,12,truncate=5)/np.maximum(db,1e-30);return (1-p)*core+p*wide,((1-p)*dc+p*db)>=.995
masks={}
for stem in LONG:
    z=np.load(SRC/f'A0_quincunx_{stem}.npz');masks[stem]=np.isfinite(z['g'])&(z['q']>0)
results=[]
for stem in TEST:
    z=np.load(SRC/f'A0_quincunx_{stem}.npz');g=z['g'];valid=np.isfinite(g)&(z['q']>0);truth,mass=broad_correction(g,valid)
    for variant in variants:
        start=time.time();model,mgood=auxiliary(stem,variant)
        for mask_name,mask in masks.items():
            kept=valid&mask;fill=(~kept)&mgood;completed=np.where(kept,g,np.where(fill,model,0));estimate,support=broad_correction(completed,kept|fill);regions=[]
            for lo,hi in [(0,350),(415,435),(435,449)]:
                target=(rad>=lo)&(rad<hi)&valid&(mass>=.995);good=target&(support>=.995);error=estimate[good]-truth[good];fraction=float(good.sum()/max(target.sum(),1));qs=np.percentile(abs(error),[50,95,99,100]).tolist() if good.any() else [None]*4;passed=bool(good.any() and qs[0]<=5 and qs[1]<=25 and fraction>=.8);regions.append(dict(radius=[lo,hi],support_fraction=fraction,median_abs_G=qs[0],p95_abs_G=qs[1],p99_abs_G=qs[2],max_abs_G=qs[3],median_signed_G=float(np.median(error)) if good.any() else None,PASS=passed))
            results.append(dict(stem=stem,variant=variant,solar_eligible=solar[stem]['eligible'],mask_from_RAW=mask_name,regions=regions));save('C0_completion_partial.json',dict(method=__doc__,results=results))
            if mask_name=='572A2983':
                np.savez_compressed(OUT/f'C0_map_{stem}_{variant}.npz',model=model.astype(np.float32),error=(estimate-truth).astype(np.float32),qualified=valid&(mass>=.995)&(support>=.995));print(stem,variant,[(r['radius'],round(r['median_abs_G'],2),round(r['p95_abs_G'],2),r['PASS']) for r in regions],flush=True)
        print('seconds',round(time.time()-start,2),flush=True)
save('C0_geometry_completion.json',dict(method=__doc__,results=results,variants=[dict(name=v,passing=sum(r['PASS'] for x in results if x['variant']==v for r in x['regions']),total=36,full_PASS=all(r['PASS'] for x in results if x['variant']==v for r in x['regions'])) for v in variants],status='DIAGNOSTIC_ONLY'))
