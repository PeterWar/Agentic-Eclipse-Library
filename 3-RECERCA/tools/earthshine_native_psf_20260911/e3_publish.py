"""Publish the verified, reversible V49 sampling correction once."""
from full_delta_common import *
from photoshop_full_api import jsx
import shutil
expected='21896b1b40bfd2ba0c13aec07491bebbaf05f4f91dbe2698957e392b3928bc2d'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for name in ['E0_verify.json','E0_readback.json','E2_actual_protection.json']:assert json.loads((OUT/name).read_text())['PASS'],name
assert json.loads((OUT/'C5_retention.json').read_text())['no_lost_old_triples']
assert json.loads((PARENT/'Z0_preservation.json').read_text())['PASS']
src=OUT/'Earthshine_V49.psb';dst=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V49.psb')
assert sha(src)==expected and not dst.exists()
with src.open('rb') as r,dst.open('xb') as w:shutil.copyfileobj(r,w,16*1024*1024)
assert sha(dst)==expected
receipt=dict(path=str(dst),sha256=expected,bytes=dst.stat().st_size,version=49,layers=26,original_layers_exact=25,canvas=[10551,7506],depth=16,photoshop=True,pixel_readback_max_DN16=3,scope='Reversible source-level green-lattice interpolation correction before the unchanged V48 CameraRaw recipe; inherited masks and original layers retained. Modest photographic improvement; no complete all-limb recovery claim.',PASS=True,PASS_scope='File, original layer preservation, native Photoshop recomposition and no lost photographic retention triples',scientific_all_limb_PASS=False)
save('E3_publish.json',receipt)
before=json.loads((PARENT/'C0_documents_before.json').read_text())['state'].splitlines()
js='var d=app.open(new File('+json.dumps(str(dst))+'));var a=[];for(var i=0;i<app.documents.length;i++){var q=app.documents[i];a.push(q.id+"|"+q.name+"|"+q.saved);}a.join("\\n");'
state=jsx(js);lines=state.splitlines();assert all(v in lines for v in before) and len(lines)==len(before)+1 and any('|Earthshine_V49.psb|true' in v for v in lines)
save('E3_open_documents.json',dict(state=state,originals_preserved=True,new_document_is_published_user_delivery=True))
print(json.dumps(receipt,ensure_ascii=False),flush=True)
