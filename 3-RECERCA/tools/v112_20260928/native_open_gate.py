"""Run the established Photoshop open gate serially, restoring user settings."""
from pathlib import Path
import json,subprocess,sys,datetime
from porta_v112 import R,sha
p=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
assert p.is_file() and not out.exists()
def js(code):
 return subprocess.run(['osascript','-e','tell application id "com.adobe.Photoshop" to do javascript '+json.dumps(code)],text=True,capture_output=True,check=True).stdout.strip()
state=js("app.displayDialogs.toString()+'|'+(app.documents.length?app.activeDocument.id:'null')").split('|')
prior=dict(dialogs=state[0],doc=None if state[1]=='null' else int(state[1]))
before=sha(p)
try:
 r=subprocess.run(['zsh',str(R/'3-RECERCA/tools/capes_totals_v14/porta_photoshop.sh'),str(p)],text=True,capture_output=True)
finally:
 code='app.displayDialogs='+prior['dialogs']+';'
 if prior['doc'] is not None:code+='for(var i=0;i<app.documents.length;i++)if(app.documents[i].id=='+str(prior['doc'])+')app.activeDocument=app.documents[i];'
 js(code)
after=sha(p)
ev=dict(file=str(p),sha256=after,source_unchanged=before==after,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,restored_settings=prior,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS' if r.returncode==0 and r.stdout.startswith('OBRE ') and before==after else 'FAIL')
out.write_text(json.dumps(ev,indent=2)+'\n');print(ev['status'],r.stdout);sys.exit(ev['status']!='PASS')
