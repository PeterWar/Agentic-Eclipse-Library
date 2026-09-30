"""Reproduce the full-rectangle C1 check after b3_full_native.py completes."""
from c0_gradient_pilot import *
g,w,names=inputs(OUT/'full_epoch2');res={};arrays={}
for mode in ['linear','log']:
    for length in [8,16]:
        a,base,cov=solve(g,w,length,mode=='log');key=mode+str(length);arrays[key]=a
        res[key]=dict(negative=int((a<=0).sum()),range=[float(a.min()),float(a.max())],top=metrics(a[215:300,585:815]))
arrays['base']=np.sum(w*np.nan_to_num(g),0)/w.sum(0);arrays['short']=g[names.index('572A2976')]
np.savez_compressed(OUT/'C1_full_epoch2.npz',**arrays);(OUT/'C1_full_epoch2.json').write_text(json.dumps(res,indent=2))
