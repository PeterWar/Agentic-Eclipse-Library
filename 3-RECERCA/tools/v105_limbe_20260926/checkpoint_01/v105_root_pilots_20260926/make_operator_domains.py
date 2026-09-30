from pathlib import Path
import numpy as np,json
O=Path('/private/tmp/v105_root_pilots_20260926');p=O/'P05';assert not p.exists();p.mkdir()
a=np.load(O/'P03/Q_OBSERVED.npz');b=np.load(O/'P04/Q_OBSERVED.npz');q={k:a[k] for k in a.files}
for k in ['F','L_scalar','scalar_observed','scalar_valid']:q[k]=b[k]
q['L_domain']=b['domini'];q['G_domain']=a['domini'];q['domini']=a['domini']
q['L_beta']=b['beta'];q['L_dins_franja']=b['dins_franja']
np.savez_compressed(p/'Q_OBSERVED.npz',**q)
rep={'G_V':'P03 post-matrix green intensity: new measuredG joins oldG12–25. No L/G conversion.','L_scalar':'P04 actual observed L joins oldL12–25 in same units.','F':'Original V104 unchanged RGB reference; E3 explicitly uses L_scalar.','domains':'domini=G_domain for G/V operators; L_domain,L_beta for E3. Both based on identical observed geometric support, with channel-specific positivity only.','source_physical_data':'P02 frozen calibration, nofloor,undoPhi, noT; E_observed unchanged.','G_and_L_domains_differ_pixels':int((q['G_domain']!=q['L_domain']).sum()),'not_validated':'Native filter/composite null and injection QA pending.'}
(p/'OPERATOR_DOMAINS.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep,indent=2))
