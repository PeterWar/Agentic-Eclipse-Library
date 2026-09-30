"""Verify all consumed RAW hashes, originals, preferences and live document state."""
from detail_common import *
from photoshop_api import jsx

def rec(p):
    p=Path(p)
    with p.open('rb') as f:
        h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h)

native=json.loads((OUT/'B0_all_native.json').read_text())
assert native['complete88'] and len(native['frames'])==88
raw=[]
for m in native['frames']:
    r=rec(m['raw_path']);assert r['sha256']==m['raw_sha256'],r['path'];raw.append(r)
assert len({r['path'] for r in raw})==88
print('RAW 88/88 byte-exact',flush=True)
base=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors')
originals=[]
for name,h in [('Earthshine_V46_Detall.psb','0af484cb7f1919900a51267f053467974c57902414258e67f54fe98638d2eb3a'),('Earthshine_V47.psb','cd30789f64d4b6f736d176ff5eaac2f76a3ebbb546661d3b117462d26fca6227')]:
    r=rec(base/name);assert r['sha256']==h,name;originals.append(r)
pub=json.loads((OUT/'C8_publish.json').read_text());assert rec(pub['path'])['sha256']==pub['sha256']
prefs=[]
for name in ['Previous.xmp','Preferences.xmp','Clipboard.xmp']:
    p=Path('/Users/USUARI/Library/Application Support/Adobe/CameraRaw/Defaults')/name
    old=ROOT/'output/earthshine_reconstruction_20260911/settings_before'/name
    assert p.read_bytes()==old.read_bytes(),name;prefs.append(rec(p))
state=jsx('var a=[];for(var i=0;i<app.documents.length;i++)a.push(app.documents[i].id+"|"+app.documents[i].name+"|"+app.documents[i].saved);a.join("\\n");')
assert '79|Earthshine_V45_Fonts.psb|false' in state
assert '140|Earthshine_V46_Detall.psb|false' in state
assert '1297|Earthshine_V48.psb|true' in state
save('Z0_final_preservation.json',dict(PASS=True,raw_count=88,raw=raw,originals=originals,camera_raw_preferences_exact=prefs,live_documents=state,publication=pub))
print('Originals, preferences, publication and live documents PASS',flush=True)
