"""Same frozen-correction factorial, using identical full-weight pixel footprints.
This excludes floor/ceiling-ramp selection from calibration on BOTH sides.
"""
from pathlib import Path
path=Path('/private/tmp/v105_qa_20260926/factorial_frozen_corrections.py');code=path.read_text()
old="""        a,sec=cells(pooledN,pooledW,cell);rd={}
        for j in [10,16]:
            b,_=cells(refs[j],inputs[j]['w'],cell);rd[meta['frames'][j]['name']]=compare(a,b,sec)"""
new="""        rd={}
        for j in [10,16]:
            expected_pool=sum(meta['frames'][k]['exposure'] for k in range(8))*np.array([1,2,1])
            expected_ref=meta['frames'][j]['exposure']*np.array([1,2,1])
            common=(pooledW>=.98*expected_pool).all(-1)&(inputs[j]['w']>=.98*expected_ref).all(-1)
            a,sec=cells(np.where(common[:,None],pooledN,0),np.where(common[:,None],pooledW,0),cell)
            b,_=cells(np.where(common[:,None],refs[j],0),np.where(common[:,None],inputs[j]['w'],0),cell)
            result=compare(a,b,sec)
            result['full_weight_common_pixels']=int(common.sum())
            result['all_fit_region_pixels']=len(common)
            rd[meta['frames'][j]['name']]=result"""
assert code.count(old)==1;code=code.replace(old,new)
code=code.replace("'factorial_frozen_corrections.json'","'factorial_frozen_corrections_plateau.json'")
exec(compile(code,str(path),'exec'),{'__name__':'__main__','__file__':str(path)})
