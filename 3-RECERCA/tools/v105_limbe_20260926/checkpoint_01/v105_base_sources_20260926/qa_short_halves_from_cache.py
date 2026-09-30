from pathlib import Path
p=Path('/private/tmp/v105_base_sources_20260926/qa_short_halves.py');s=p.read_text();ns={};exec(s.split('groups=')[0],ns);globals().update(ns)
groups={'alternate_A':[0,2,4,6],'alternate_B':[1,3,5,7],'early_A':[0,1,2,3],'late_B':[4,5,6,7]};acc={}
for k in groups:
 q=np.load(O/f'SHORT_HALF_{k}.npz');a={c:q[c] for c in ['E','W','NF','NEFF','DRMIN','DRMAX']};a['valid']=np.isfinite(a['E']).all(-1);acc[k]=a
exec('def hp('+s.split('def hp(',1)[1])
