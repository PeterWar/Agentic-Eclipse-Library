"""Read-only preservation check; archival UI snapshot is not a new style target."""
from joint_common import *
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import shutil,subprocess
HERE=Path(__file__).resolve().parent
def rec(p):
    p=Path(p)
    with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
prior_path=ROOT/'research/tools/earthshine_optics_20260911/delivery_manifest.json';prior=json.loads(prior_path.read_text())
oldcanon=prior['canonical_after']+[prior['handoff']]
for a in oldcanon:assert rec(a['path'])['sha256']==a['sha256'],('Authority changed',a['path'])
snap=HERE/'docs_before';snap.mkdir(exist_ok=True)
for i,a in enumerate(oldcanon):
    target=snap/(str(i)+'_'+Path(a['path']).name)
    if target.exists():assert rec(target)['sha256']==a['sha256']
    else:shutil.copy2(a['path'],target)
with ThreadPoolExecutor(max_workers=3) as pool:consumed=list(pool.map(rec,[a['path'] for a in prior['inputs']]))
expected={a['path']:a['sha256'] for a in prior['inputs']}
for a in consumed:assert a['sha256']==expected[a['path']],('Source changed',a['path'])
pub=rec(prior['publication']['path']);assert pub['sha256']==prior['publication']['sha256']
base=Path(pub['path']).parent;originals=[]
for name,sha in [('Earthshine_V46_Detall.psb','0af484cb7f1919900a51267f053467974c57902414258e67f54fe98638d2eb3a'),('Earthshine_V47.psb','cd30789f64d4b6f736d176ff5eaac2f76a3ebbb546661d3b117462d26fca6227')]:
    a=rec(base/name);assert a['sha256']==sha;originals.append(a)
prefs=[]
for name in ['Previous.xmp','Preferences.xmp','Clipboard.xmp']:
    p=Path('/Users/USUARI/Library/Application Support/Adobe/CameraRaw/Defaults')/name;assert p.read_bytes()==(ROOT/'output/earthshine_reconstruction_20260911/settings_before'/name).read_bytes();prefs.append(rec(p))
js='var a=[];for(var i=0;i<app.documents.length;i++)a.push(app.documents[i].id+"|"+app.documents[i].name+"|"+app.documents[i].saved);a.join("\\n");'
sc='tell application id "com.adobe.Photoshop"\ndo javascript '+json.dumps(js)+'\nend tell'
state=subprocess.check_output(['osascript','-e',sc],text=True).strip()
save('Z0_preservation.json',dict(PASS=True,created=datetime.now(timezone.utc).isoformat(),consumed_sources_exact=consumed,publication_unchanged=pub,originals=originals,camera_raw_preferences_exact=prefs,live_documents=state,canonical_before=oldcanon,prior_manifest=rec(prior_path),style_reference='Saved V48 disk product; user explicitly clarified live visibility changes were inspection only',archive_snapshot='V48_live_before_joint.psd is archival, not canonical and not a new preferred aesthetic',scope='Native88 arrays and other sources93 checked; V46/V47/V48 files and three CameraRaw settings exact. RAW88 not reopened or modified; inherited V48 RAW hashes retain their original scope. No new PSB, no live original saved or closed.'))
print('PRESERVATION PASS',len(consumed),'source files',state,flush=True)
