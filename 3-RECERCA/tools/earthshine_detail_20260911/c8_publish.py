"""Publish the verified V48 once; preserve every existing photographic file."""
from detail_common import *
from photoshop_api import jsx
import shutil

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

expected='48715be427ebd5ea654eeea746e0a295201f9f0a354e4f5e37fbf40df47443a5'
src=OUT/'Earthshine_V48.psb'
dst=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V48.psb')
assert sha(src)==expected
for name in ['C4_verify.json','C4_readback.json','C7_actual_protection.json']:
    assert json.loads((OUT/name).read_text())['PASS'], name
assert not json.loads((OUT/'C6_retention_changes.json').read_text())['loss']
assert not dst.exists(), str(dst)
with src.open('rb') as r, dst.open('xb') as w:
    shutil.copyfileobj(r,w,16*1024*1024)
assert sha(dst)==expected
receipt=dict(path=str(dst),sha256=expected,bytes=dst.stat().st_size,version=48,
    layers=25,original_layers_exact=24,canvas=[10551,7506],depth=16,
    photoshop=True,pixel_readback_max_DN16=3,
    scope='Photographic update from all67 refreshed Vixen sources; all21 Sony sources separately refreshed and used for independent source controls. Legacy coarse photographic layer retains both trains. No new mask; no complete all-limb recovery claim.')
save('C8_publish.json',receipt)
# Open the new saved file without saving, closing or changing any prior document.
js='var d=app.open(new File('+json.dumps(str(dst))+'));var a=[];for(var i=0;i<app.documents.length;i++)a.push(app.documents[i].id+"|"+app.documents[i].name+"|"+app.documents[i].saved);a.join("\\n");'
state=jsx(js)
assert '79|Earthshine_V45_Fonts.psb|false' in state
assert '140|Earthshine_V46_Detall.psb|false' in state
save('C8_open_documents.json',dict(state=state))
print(json.dumps(receipt,ensure_ascii=False),flush=True)
print(state,flush=True)
