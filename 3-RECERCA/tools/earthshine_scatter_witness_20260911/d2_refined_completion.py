"""Refined auxiliary completion: no observed bright rim as latent lunar light.
Use measured deep-Moon scalar only in the auxiliary hidden-light model, plus
a bounded smooth coronal continuation across at most8px of missing support.
Four new short RAWs and real long-exposure validity masks test the result.
"""
from scatter_common import *
import ast,time,cv2
from scipy.ndimage import gaussian_filter,distance_transform_edt
new_stems=['572A2967','572A2985','572A2997','572A3003'];plan=json.loads((OUT/'PLAN.json').read_text());excluded=sorted(set(plan['reserved_stems']+new_stems));save('D2_refined_plan.json',dict(method=__doc__,training_excluded=excluded,new_validation_RAW=new_stems,actual_long_mask_RAW=['572A2978','572A2980','572A2983'],auxiliary_moon='Measured weighted median of deepMoon r<350, only to estimate unobserved light entering wide kernel; never replaces measured source pixels',auxiliary_corona='Normalized Gaussian sigma4 continuation only within8px of genuine measured support; modelled light, not measured coronal texture',gates='Each new epoch/mask/radius:median absolute wide-correction error<=5G,p95<=25G,support>=0.80. Same numerical limits asD0, now masks independent of reserved short noise.',motivation='D1 repeated the observed contaminated lunar rim as latent light, then blurred it again; and no coronal continuation left narrow support holes. New masks avoid truncating positive noise in faint short exposures.',status='Diagnostic only; no PSB or original source change'))
# Reuse exactly the training-only HDR builder with a new, larger exclusion set
# and unique output names; do not overwrite the prior D0 experiment.
code=(HERE/'d0_completion_sources.py').read_text();code=code.replace("reserved=set(plan['reserved_stems'])","reserved=set(plan['reserved_stems']+new_stems)");code=code.replace("D0_completion_","D2_training_");exec(compile(code,str(HERE/'d0_completion_sources.py'),'exec'))
src=np.load(OUT/'D2_training_sources.npz');frames={r['stem']:r for r in json.loads((OUT/'D2_training_sources.json').read_text())['frames']};yy,xx=np.mgrid[:N,:N].astype(np.float32);rad=np.hypot(xx-CX,yy-CY);distance=src['source_lunar_distance'];P=np.clip(.5-distance,0,1);moon=float(np.nanmedian(src['lunar'][rad<350]));cv=np.isfinite(src['solar']);Cg=np.nan_to_num(src['solar']);gap=distance_transform_edt(~cv);den=gaussian_filter(cv.astype(float),4,truncate=5);smooth=gaussian_filter(Cg,4,truncate=5)/np.maximum(den,1e-30);extended=(~cv)&(gap<=8)&(den>=1e-5);Ce=np.where(cv,Cg,np.where(extended,smooth,0));validc=cv|extended;p=json.loads((OUT/'B1_physical_mixture.json').read_text())['p'];a=p/(1-p);coeff=np.array([a,-a*a,a**3,-a**4])
np.savez_compressed(OUT/'D2_auxiliary_corona.npz',solar=Ce,valid=validc,measured=cv,extended=extended,moon_level=moon)
def auxiliary(stem):
    center=frames[stem]['solar_center'];mx=xx-np.float32(center[0]-CX);my=yy-np.float32(center[1]-CY);solar=cv2.remap(Ce.astype(np.float32),mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);good=cv2.remap(validc.astype(np.float32),mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)>=1-1e-6;cover=P+(1-P)*good;F=P*moon+(1-P)*solar*good;dc=gaussian_filter(cover,.97,truncate=5);core=gaussian_filter(F,.97,truncate=5)/np.maximum(dc,1e-30);db=gaussian_filter(dc,12,truncate=5);wide=gaussian_filter(core*dc,12,truncate=5)/np.maximum(db,1e-30);return (1-p)*core+p*wide,((1-p)*dc+p*db)>=.995
# Reuse the wide correction function without importing the D0 source state.
tree=ast.parse((HERE/'completion.py').read_text());fn=next(r for r in tree.body if isinstance(r,ast.FunctionDef) and r.name=='broad_correction');exec(compile(ast.Module(body=[fn],type_ignores=[]),str(HERE/'completion.py'),'exec'))
masks={}
for stem in ['572A2978','572A2980','572A2983']:
    z=np.load(SRC/f'A0_quincunx_{stem}.npz');masks[stem]=np.isfinite(z['g'])&(z['q']>0)
results=[]
for stem in new_stems:
    start=time.time();z=np.load(SRC/f'A0_quincunx_{stem}.npz');g=z['g'];valid=np.isfinite(g)&(z['q']>0);truth,mass=broad_correction(g,valid);model,good_model=auxiliary(stem)
    for mask_name,mask in masks.items():
        kept=valid&mask;fill=(~kept)&good_model;completed=np.where(kept,g,np.where(fill,model,0));estimate,support=broad_correction(completed,kept|fill);regions=[]
        for lo,hi in [(0,350),(415,435),(435,449)]:
            target=(rad>=lo)&(rad<hi)&valid&(mass>=.995);good=target&(support>=.995);error=estimate[good]-truth[good];fraction=float(good.sum()/max(target.sum(),1));q=np.percentile(abs(error),[50,95,99,100]).tolist() if good.any() else [None]*4;passed=bool(good.any() and q[0]<=5 and q[1]<=25 and fraction>=.8);regions.append(dict(radius=[lo,hi],target_pixels=int(target.sum()),qualified_pixels=int(good.sum()),support_fraction=fraction,median_abs_G=q[0],p95_abs_G=q[1],p99_abs_G=q[2],max_abs_G=q[3],median_signed_G=float(np.median(error)) if good.any() else None,PASS=passed))
        r=dict(stem=stem,mask_from_RAW=mask_name,regions=regions);results.append(r);save('D2_refined_validation_partial.json',dict(method=__doc__,frames=results));print(stem,mask_name,[(a['radius'],round(a['support_fraction'],3),round(a['median_abs_G'],2),round(a['p95_abs_G'],2),a['PASS']) for a in regions],flush=True)
    print(stem,'seconds',round(time.time()-start,2),flush=True)
passed=all(a['PASS'] for r in results for a in r['regions']);save('D2_refined_validation.json',dict(method=__doc__,new_reserved_RAW=new_stems,excluded_training_RAW=excluded,moon_auxiliary_level=moon,coronal_continuation_pixels=int(extended.sum()),frames=results,completion_PASS=passed,limits=['Coronal8px continuation and deep-Moon scalar are auxiliary nuisance assumptions, never measured texture','Tests use new RAWs and actual long-exposure validity patterns but not all actual exposure geometries','No completed pixel enters a source as recovered data; only measured native pixels may be corrected after all gates']))
print('DONE36',passed,flush=True)
