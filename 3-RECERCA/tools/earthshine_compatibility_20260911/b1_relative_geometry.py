from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'output/earthshine_compatibility_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_COMPATIBILITY_20260911'
d=json.loads((out/'B0_geometry.json').read_text());edges=[r for r in d['pairs'] if r['translation']['pass_halves']];nodes={2976}
while True:
 old=nodes.copy()
 for r in edges:
  if r['reference'] in nodes or r['moving'] in nodes:nodes.update([r['reference'],r['moving']])
 if old==nodes:break
ns=sorted(nodes-{2976});A=[];b=[];links=[]
for r in edges:
 a,c=r['reference'],r['moving']
 if a not in nodes or c not in nodes:continue
 row=np.zeros(len(ns))
 if a!=2976:row[ns.index(a)]-=1
 if c!=2976:row[ns.index(c)]+=1
 A.append(row);b.append(r['translation']['fit']['parameters']);links.append([a,c])
x=np.linalg.lstsq(A,b,rcond=None)[0];res=np.array(A)@x-np.array(b)
shifts={'2976':[0.,0.]};shifts.update({str(n):(-v).tolist() for n,v in zip(ns,x)})
r=dict(anchor=2976,source_shifts=shifts,links=[dict(nodes=e,residual=float(np.linalg.norm(r))) for e,r in zip(links,res)],fit_residual_max=float(np.linalg.norm(res,axis=1).max()),scope='Exploratory relative graph. Accepted individual edges do not establish a cross-epoch bridge without independent cycle validation. Absolute lunar mapping remains to be checked.',unconnected=[m['frame'] for m in json.loads((out/'B0_patch_meta.json').read_text())['frames'] if int(m['frame'][4:8]) not in nodes])
(out/'B1_relative_geometry.json').write_text(json.dumps(r,indent=2))
