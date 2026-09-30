from pathlib import Path
import numpy as np,json,pandas as pd
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';d=json.loads((O/'S14_multiband_detection.json').read_text());rows=[];sets={k:{(r['kind'],r['TYC']):r for r in v['rows'] if r['kind']!='psf_reference'} for k,v in d.items()};allkeys=sorted(set(sets['Sony'])|set(sets['Vixen']));counts={}
for key in allkeys:
 s=sets['Sony'].get(key);v=sets['Vixen'].get(key);ref=s or v;ss=max(s['native']['all']['snr'],s['multiband']['all']['snr']) if s else 0;sv=max(v['native']['all']['snr'],v['multiband']['all']['snr']) if v else 0;joint=ss>=4 and sv>=4 and np.hypot(ss,sv)>=8;accept=bool((s and s['union_accept']) or (v and v['union_accept']) or joint);inside=0<=ref['x_final']<10551 and 0<=ref['y_final']<7506
 rows.append(dict(kind=key[0],TYC=key[1],HIP=ref.get('HIP'),V=ref['V'],BV=ref['BV'],x=ref['x_final'],y=ref['y_final'],inside=bool(inside),Sony_SNR=float(ss),Vixen_SNR=float(sv),joint_two_trains=bool(joint),accepted=accept,Sony_source=s,Vixen_source=v))
for kind in ['catalog','rotated_null']:counts[kind]=dict(tested=sum(r['kind']==kind for r in rows),accepted=sum(r['kind']==kind and r['accepted'] for r in rows),inside_accepted=sum(r['kind']==kind and r['accepted'] and r['inside'] for r in rows));print(kind,counts[kind])
# Duplicate source safeguard: catalogue proximity is not evidence of two resolved point sources.
sel=[r for r in rows if r['kind']=='catalog' and r['accepted'] and r['inside']];pairs=[]
for i,r in enumerate(sel):
 for q in sel[:i]:
  dd=np.hypot(r['x']-q['x'],r['y']-q['y'])
  if dd<12:pairs.append(dict(TYC=[r['TYC'],q['TYC']],separation_final_px=float(dd)))
old=json.loads((R/'output/v58_correccions_20260913/D4_sources.json').read_text())['selected'];missing=[];names={r['TYC'] for r in sel}
for q in old:
 r=q['star'];tyc=r.get('TYC')
 if tyc not in names:missing.append(dict(TYC=tyc,old_V=r.get('Vmag'),old_xy=[r['x'],r['y']],current=next((dict(Sony_SNR=q['Sony_SNR'],Vixen_SNR=q['Vixen_SNR'],inside=q['inside']) for q in rows if q['TYC']==tyc and q['kind']=='catalog'),None)))
(O/'S15_joint_catalog.json').write_text(json.dumps(dict(counts=counts,rows=rows,nearby_pairs=pairs,previous52_not_accepted=missing,claim='Retain native per-train confirmations; additionally confirm weak sources jointly when each separate instrument has SNR>=4 and joint SNR>=8. Same source-position and reflected-position rules. No catalogue-only stars.'),indent=2));print('pairs',pairs,'missing',missing,flush=True)
