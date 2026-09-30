"""Fail-closed delivery decision, distinct from method and file-integrity gates."""
from pathlib import Path
import json,sys
from porta_v112 import O,sha,APPROVED_NATIVE,PSB
from qa_wedge import measure

def check():
 S=O/'sensor_mass301';out=dict(status='BLOCKED',delivery_approved=False,failures=[],branch='sensor_mass301')
 def ck(ok,name,**kw):
  if not ok:out['failures'].append(dict(check=name,**kw))
 evpath=S/'NATIVE_EVIDENCE.json';ev=json.loads(evpath.read_text())
 ck(sha(evpath) in APPROVED_NATIVE,'observed_native_evidence')
 p=O/'V112_CANDIDATE.psb';out['psb_sha256']=sha(p);ck(out['psb_sha256']==ev['psb_sha256'],'actual_native_PSB')
 from semantic_v112 import knee_stack_check
 semantic=knee_stack_check(json.loads((S/'TARGETS.json').read_text()),PSB(str(p)))
 out['semantic_dependency']=semantic
 ck(semantic['status']=='NECESSARY_DEPENDENCIES_PASS','knee_valid_for_active_stack',details=semantic['failures'])
 from brno_astronomical_support_v112 import check as astronomical_support
 from qa_brno import R,WINDOWS
 out['astronomical_support']=astronomical_support(R,WINDOWS)
 ck(out['astronomical_support']['status']=='SUPPORT_PASS','external_astronomical_support',details=out['astronomical_support']['failures'])
 for role in ['control','candidate','final']:
  v=ev['files'][role];ck(sha(v['path'])==v['sha256'],'frozen_native_render',role=role)
 # Always recompute the fixed seam metric; a renamed or edited QA JSON cannot approve it.
 base=measure(Path(ev['files']['control']['path']));candidate=measure(Path(ev['files']['final']['path']))
 out['fixed_seams']=[]
 for i,(a,b) in enumerate(zip(base,candidate),1):
  reduction=1-b['max_step40']/a['max_step40'];out['fixed_seams'].append(dict(seam=i,reduction=reduction))
  ck(b['max_step40']<=.5*a['max_step40'],'fixed_seam_50_percent',seam=i,reduction=reduction)
 # No promotion merely because numerical and file checks succeed.
 # This branch's marked outer structures still lack a validated independent noise model.
 ck(False,'unresolved_marked_structures',marks=[2,3,5,7,8,10,14],meaning='Causal contributions identified for8/10; complete physical separation and validated correction remain absent. Preserve data and negative results')
 if not out['failures']:
  raise RuntimeError('No promotion path is implemented for this research branch')
 return out

if __name__=='__main__':
 r=check();(O/'sensor_mass301/PORTA_LLIURAMENT.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r));sys.exit(1)
