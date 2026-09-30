"""Express heldout core prediction errors in units of local lunar brightness."""
from optics_common import *
a=json.loads((OUT/'A0_profiles.json').read_text())
fits={(m['stem'],s['angle']):s['fit'] for m in a['frames'] for s in m['sectors']}
a=json.loads((OUT/'A1_core_prediction.json').read_text());out={}
for train in ['vixen','sony']:
    rows=[r for r in a['tests'] if r['tren']==train and r['qualified']]
    errors=[r['constant']['relative_rms']*fits[r['stem'],r['angle']]['amplitude'] for r in rows]
    ratios=[error/max(abs(fits[r['stem'],r['angle']]['inside_level']),1) for error,r in zip(errors,rows)]
    out[train]=dict(absolute_profile_rms_quantiles=np.percentile(errors,[10,50,90]).tolist(),ratio_to_local_inner_brightness_quantiles=np.percentile(ratios,[10,50,90]).tolist())
save('A2_dynamic_range.json',out)
