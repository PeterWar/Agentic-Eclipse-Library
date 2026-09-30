import subprocess,json,hashlib
from pathlib import Path
R=Path.cwd();O=R/'4-RESULTATS/v85_regeneracio_20260922'
def js(code):
 script='tell application id "com.adobe.Photoshop"\n with timeout of 3600 seconds\n do javascript '+json.dumps(code)+'\n end timeout\nend tell'
 return subprocess.check_output(['osascript','-e',script],text=True).strip()
state=js("app.activeDocument.id+' '+app.displayDialogs")
(O/'PHOTOSHOP_GATE_STATE_BEFORE.txt').write_text(state)
prior_id,prior_dialogs=state.split()
assert prior_id.isdigit() and prior_dialogs in ['DialogModes.NO','DialogModes.ALL','DialogModes.ERROR']
try:
 p=subprocess.run(['zsh',str(R/'3-RECERCA/tools/capes_totals_v14/porta_photoshop.sh'),str(R/'1-PHOTOSHOP/V85.psb')],text=True,capture_output=True)
 (O/'PHOTOSHOP_GATE.txt').write_text(p.stdout+p.stderr);assert p.returncode==0 and 'OBRE 10551 px x 7506 px · 42 capes' in p.stdout,p.stdout
finally:js('for(var i=0;i<app.documents.length;i++)if(app.documents[i].id=='+prior_id+')app.activeDocument=app.documents[i];app.displayDialogs='+prior_dialogs+';"RESTORED"')
h=hashlib.sha256();dst=R/'1-PHOTOSHOP/V85.psb'
with dst.open('rb') as f:
 while b:=f.read(16<<20):h.update(b)
expected=json.loads((O/'NATIVE_INTEGRITY.json').read_text())['native_sha256'];assert h.hexdigest()==expected
(O/'PHOTOSHOP_GATE.json').write_text(json.dumps({'PASS':True,'result':p.stdout.strip(),'sha256':expected,'bytes':dst.stat().st_size,'prior_active_document_and_dialogs_restored':True},indent=2)+'\n');print(p.stdout.strip())
