"""Verify old sources, original PSBs, current authority and CameraRaw settings."""
from native_common import *
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from photoshop_api import jsx
import shutil
HERE=Path(__file__).resolve().parent
def rec(p):
    p=Path(p)
    with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
prior_path=ROOT/'research/tools/earthshine_joint_20260911/delivery_manifest.json';prior=json.loads(prior_path.read_text());canon=prior['canonical_after']+[prior['handoff']]
snap=HERE/'docs_before';snap.mkdir(exist_ok=True)
for i,a in enumerate(canon):
    assert rec(a['path'])['sha256']==a['sha256'],('Authority changed',a['path'])
    target=snap/(str(i)+'_'+Path(a['path']).name)
    if target.exists():assert rec(target)['sha256']==a['sha256']
    else:shutil.copy2(a['path'],target)
with ThreadPoolExecutor(max_workers=3) as pool:inputs=list(pool.map(rec,[a['path'] for a in prior['inputs']]))
expected={a['path']:a['sha256'] for a in prior['inputs']}
for a in inputs:assert a['sha256']==expected[a['path']],a['path']
originals=[];base=Path(prior['publication']['path']).parent
for name,sha in [('Earthshine_V46_Detall.psb','0af484cb7f1919900a51267f053467974c57902414258e67f54fe98638d2eb3a'),('Earthshine_V47.psb','cd30789f64d4b6f736d176ff5eaac2f76a3ebbb546661d3b117462d26fca6227'),('Earthshine_V48.psb','48715be427ebd5ea654eeea746e0a295201f9f0a354e4f5e37fbf40df47443a5')]:
    a=rec(base/name);assert a['sha256']==sha;originals.append(a)
settings=[]
for name in ['Previous.xmp','Preferences.xmp','Clipboard.xmp']:
    p=Path('/Users/USUARI/Library/Application Support/Adobe/CameraRaw/Defaults')/name;assert p.read_bytes()==(ROOT/'output/earthshine_reconstruction_20260911/settings_before'/name).read_bytes();settings.append(rec(p))
state=jsx('var a=[];for(var i=0;i<app.documents.length;i++){var d=app.documents[i];a.push(d.id+"|"+d.name+"|"+d.saved);}a.join("\\n");');assert state==json.loads((OUT/'C0_documents_before.json').read_text())['state'],state
raws=json.loads((OUT/'A2_all_native.json').read_text())['frames'];assert len(raws)==67 and len({m['raw_path'] for m in raws})==67
save('Z0_preservation.json',dict(PASS=True,created=datetime.now(timezone.utc).isoformat(),consumed_sources_exact=inputs,originals=originals,camera_raw_preferences_exact=settings,live_documents=state,canonical_before=canon,prior_manifest=rec(prior_path),raw67_verified_during_render=[dict(path=m['raw_path'],sha256=m['raw_sha256']) for m in raws],scope='93 frozen source files and V46/V47/V48 rehashed; RAW67 read and SHA checked during render; 21 Sony source arrays held unchanged. Own CameraRaw and gate documents closed; original live document state preserved.'))
print('PRESERVATION PASS',len(inputs),'sources; original documents preserved',flush=True)
