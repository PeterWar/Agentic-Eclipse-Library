"""Run only after the root observed native_save complete; seals provenance, not quality."""
from pathlib import Path
import json,datetime
from porta_v112 import R,O,sha
T=Path(__file__).parent
S=O/'sensor_mass301';dst=O/'V112_CANDIDATE.psb'
assert dst.is_file() and not (S/'NATIVE_EVIDENCE.json').exists()
files={}
def add(k,p):files[k]=dict(path=str(p.resolve()),sha256=sha(p))
for role,folder in [('control',O/'control_natiu'),('candidate',S/'candidate_natiu'),('control_off',O/'control_off'),('candidate_off',S/'candidate_off'),('final',S/'final_natiu')]:
 log=folder/('NATIU.log' if role=='final' else 'RENDER.log')
 text=log.read_text();assert 'COMPLET' in text and 'ERROR' not in text
 add(role,folder/'visible_complet.tif');add(role+'_log',log)
 add(role+'_jsx',folder/('desa_natiu.jsx' if role=='final' else 'render.jsx'))
add('control_stage',O/'V111_control_stage.psb');add('candidate_stage',S/'V112_mass301_stage.psb')
for key,path in [('source',O.parent/'v110_torre_20260928/V111.psb'),('lineage',S/'LINEAGE.json'),('targets',S/'TARGETS.json'),('native_render_template',T/'native_render.py'),('native_save_template',T/'native_save.py')]:add(key,path)
ev=dict(schema='V112-observed-native-envelope-1',observed_by='Codex root, serial Photoshop native_save tool completed',sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),psb_sha256=sha(dst),files=files,scientific_status='QUALITY_FAIL_NOT_FOR_PROMOTION')
p=S/'NATIVE_EVIDENCE.json';p.write_text(json.dumps(ev,indent=2)+'\n')
print(sha(p),flush=True)
