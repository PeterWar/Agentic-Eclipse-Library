"""Artificially censor reserved short exposures and predict their broad light.
Ground truth is the same short exposure's actually observed broad predictor;
the completion sources exclude all reserved RAWs.
"""
from completion import *
import time
rows=[r for r in json.loads((OUT/'A0_witness_inputs.json').read_text())['frames'] if not r['train']];results=[];aggregates={}
for row in rows:
    stem=row['stem'];start=time.time();z=np.load(SRC/f'A0_quincunx_{stem}.npz');g=z['g'];valid=np.isfinite(g)&(z['q']>0);truth,mass=broad_correction(g,valid);model,mgood=auxiliary(stem)
    for threshold in [1000,5000,20000]:
        kept=valid&(g<=threshold);fill=(~kept)&mgood;completed=np.where(kept,g,np.where(fill,model,0));comp_valid=kept|fill;estimate,support=broad_correction(completed,comp_valid);regions=[]
        for lo,hi in [(0,350),(415,435),(435,449)]:
            target=(r>=lo)&(r<hi)&valid&(mass>=.995);qualified=target&(support>=.995);total=int(target.sum());count=int(qualified.sum());error=estimate[qualified]-truth[qualified];abs_error=abs(error);quant=np.percentile(abs_error,[50,95,99,100]).tolist() if count else [None]*4;regions.append(dict(radius=[lo,hi],target_pixels=total,qualified_pixels=count,support_fraction=count/max(total,1),median_abs_G=quant[0],p95_abs_G=quant[1],p99_abs_G=quant[2],max_abs_G=quant[3],median_signed_G=float(np.median(error)) if count else None));key=(row['epoch'],threshold,lo,hi);aggregates.setdefault(key,dict(errors=[],target=0,qualified=0));a=aggregates[key];a['errors'].append(error.astype(np.float32));a['target']+=total;a['qualified']+=count
        results.append(dict(stem=stem,epoch=row['epoch'],artificial_threshold_G=threshold,regions=regions));save('D1_completion_validation_partial.json',dict(method=__doc__,frames=results));print(stem,'threshold',threshold,[(x['radius'],round(x['support_fraction'],3),None if x['p95_abs_G'] is None else round(x['p95_abs_G'],2)) for x in regions],flush=True)
    print(stem,'seconds',round(time.time()-start,2),flush=True)
summary=[]
for (epoch,threshold,lo,hi),v in aggregates.items():
    errors=np.concatenate(v['errors']);fraction=v['qualified']/max(v['target'],1);quant=np.percentile(abs(errors),[50,95,99,100]).tolist() if len(errors) else [None]*4;passed=bool(len(errors) and quant[0]<=5 and quant[1]<=25 and fraction>=.8);summary.append(dict(epoch=epoch,threshold_G=threshold,radius=[lo,hi],target_pixels=v['target'],qualified_pixels=v['qualified'],support_fraction=fraction,median_abs_G=quant[0],p95_abs_G=quant[1],p99_abs_G=quant[2],max_abs_G=quant[3],PASS=passed))
passed=all(r['PASS'] for r in summary);save('D1_completion_validation.json',dict(method=__doc__,summary=summary,frames=results,completion_PASS=passed,limits=['Artificial masks approximate brightness censoring; original RAW calibration/linearity is unchanged','Completion is auxiliary only and contains no recovered texture at censored pixels','This does not validate every actual long-exposure mask or PSF core; those must be checked before photographic promotion']))
print('DONE',len(summary),'gates','PASS',passed,flush=True)
