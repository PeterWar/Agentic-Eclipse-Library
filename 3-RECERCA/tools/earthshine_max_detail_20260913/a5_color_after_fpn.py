"""Combine independently reconstructed colors after their own detector fit.
Frozen A3 scalar texture scales and training photon fractions; no Sony fit.
All variants retained, including potentially harmful blue ablation.
"""
from common import *
claim();m=json.loads((OUT/'A3_model_frozen.json').read_text());q=json.loads((OUT/'A3_candidates.json').read_text())['RGB_median_weights'];weights={'R':q['R'],'G':q['G1']+q['G2'],'B':q['B']};weights={k:v/sum(weights.values()) for k,v in weights.items()};slopes={'R':m['slopes']['R'],'G':1.,'B':m['slopes']['B']};offsets={'R':m['offsets']['R'],'G':0.,'B':m['offsets']['B']}
save('A5_color_model.json',dict(method=__doc__,weights=weights,slopes=slopes,offsets=offsets,source_model='B3 channel67 robust, each channel own calibrated-radiance detector field; this is source analysis, not a full photographic color replacement',primary='RGB_fpn',ablations=['G_baseline','G_fpn','GR_baseline','GR_fpn','RGB_baseline','RGB_fpn','B_fpn','R_fpn']))
base={};fpn={}
for c in 'GRB':
    z=np.load(OUT/'arrays'/f'B3_{c}67_robust_all.npz');base[c]=z['raw_baseline']/slopes[c]+offsets[c];fpn[c]=z['source']/slopes[c]+offsets[c]
arr={}
for suffix,d in [('baseline',base),('fpn',fpn)]:
    for label,cc in [('G',['G']),('GR',['G','R']),('RGB',['G','R','B']),('R',['R']),('B',['B'])]:
        arr[label+'_'+suffix]=(sum(weights[c]*d[c] for c in cc)/sum(weights[c] for c in cc)).astype(np.float32)
np.savez_compressed(OUT/'arrays/A5_color_after_fpn.npz',**arr)
print('A5 colors frozen',weights,flush=True)
