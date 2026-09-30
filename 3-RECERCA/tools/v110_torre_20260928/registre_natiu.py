"""Bind the owned Photoshop evidence to actual files, then run the method gate."""
from pathlib import Path
import sys, json, hashlib, subprocess, datetime
ROOT = Path(__file__).resolve().parents[3]
O = ROOT/'4-RESULTATS/v110_torre_20260928'
def sha(p):
    with open(p, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
files = {'control_stage': O/'control_stage.psb', 'candidate_stage': O/'noCEL_stage.psb',
         'final_render': O/'diagnostic_natiu/visible_complet.tif',
         'final_log': O/'diagnostic_natiu/NATIU.log',
         'final_jsx': O/'diagnostic_natiu/desa_natiu.jsx'}
for prefix, folder, render_key in [
    ('control', 'control_natiu', 'control_render'),
    ('candidate', 'noCEL_natiu', 'candidate_render'),
    ('control_off', 'control_sense239_241', 'control_without_adjustments'),
    ('candidate_off', 'noCEL_sense239_241', 'candidate_without_adjustments')]:
    files[render_key] = O/folder/'visible_complet.tif'
    files[prefix+'_log'] = O/folder/'RENDER.log'
    files[prefix+'_jsx'] = O/folder/'render.jsx'
for key,p in files.items():
    if key.endswith('_log'):
        log=p.read_text()
        assert 'COMPLET' in log and 'ERROR' not in log, key
doc = O/'V110_DIAGNOSTIC.psb'
contract = O/'CONTRACTE_TORRE.json'
e = dict(delivered_sha256=sha(doc), contract_sha256=sha(contract),
         recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
         files={key:dict(path=str(p), sha256=sha(p), size=p.stat().st_size) for key,p in files.items()})
f = O/'EVIDENCIA_NATIVA.json'
f.write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
print('Evidence frozen', e['delivered_sha256'], flush=True)
subprocess.run([sys.executable, str(ROOT/'3-RECERCA/tools/guardrails_postprocessat/porta_torre_pisa.py'),
                str(doc), '--contract', str(contract), '--native', str(f),
                '--output', str(O/'PORTA_FINAL.json')], check=True)
