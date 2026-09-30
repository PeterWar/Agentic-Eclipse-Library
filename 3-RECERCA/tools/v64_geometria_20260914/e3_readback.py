from pathlib import Path
import tifffile as tf, numpy as np, json,hashlib
R=Path.cwd();O=R/'output/v64_geometria_20260914';P=R/'output/v62_prominencies_20260913'
a=tf.imread(O/'V64_candidate.tif');b=tf.imread(O/'V64_final_readback.tif')
assert a.shape==b.shape
mx=0;changed=0
for y in range(0,len(a),100):
    d=abs(a[y:y+100].astype('int32')-b[y:y+100].astype('int32'))
    mx=max(mx,int(d.max()));changed+=int(np.count_nonzero(d))
assert mx<=4,mx
rep=dict(PASS=True,shape=list(a.shape),max_DN16=mx,changed_channel_samples=changed,method='Native published PSB reopen, full-layer duplicate, force recomposite by changing foreground visibility off and on, flattened native TIFF export; source document not modified.')
pub=json.loads((O/'E0_publish.json').read_text())
with open(pub['path'],'rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
assert h==pub['sha256'];rep['published_sha256_after_reopen']=h
(O/'E3_final_readback.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep),flush=True)
