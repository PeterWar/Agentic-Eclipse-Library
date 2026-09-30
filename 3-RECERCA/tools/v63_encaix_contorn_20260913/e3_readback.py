from pathlib import Path
import tifffile as tf, numpy as np, json,hashlib
R=Path.cwd();O=R/'output/v63_encaix_contorn_20260913';P=R/'output/v62_prominencies_20260913'
a=tf.imread(O/'V63_candidate.tif');b=tf.imread(O/'V63_final_readback.tif')
assert a.shape==b.shape
mx=0;changed=0
for y in range(0,len(a),100):
    d=abs(a[y:y+100].astype('int32')-b[y:y+100].astype('int32'))
    mx=max(mx,int(d.max()));changed+=int(np.count_nonzero(d))
assert mx<=4,mx
rep=dict(PASS=True,shape=list(a.shape),max_DN16=mx,changed_channel_samples=changed,method='Native published PSB reopen, full-layer duplicate, force recomposite by changing foreground visibility off and on, flattened native TIFF export; source document not modified.')
del a
c=tf.imread(P/'V62_final_readback.tif')
print('COMPARE V62',c.shape,'V63',b.shape,flush=True)
# Compare unchanged exterior only. V62 may carry associated alpha; opaque
# RGB-only output corresponds to alpha 65535. No matte/background conversion.
ex=0;ex_changed=0
for y in range(0,len(b),100):
    yy=np.arange(y,min(y+100,len(b)))[:,None];xx=np.arange(b.shape[1])[None,:]
    outside=(xx<4377)|(xx>=6377)|(yy<2777)|(yy>=4777)
    d=abs(c[y:y+100,...,:3].astype('int32')-b[y:y+100,...,:3].astype('int32'))
    ex=max(ex,int(d[outside].max()));ex_changed+=int(np.count_nonzero(d[outside]))
rep['outside_lunar_ROI_RGB_max_DN16']=ex;rep['outside_lunar_ROI_changed_channel_samples']=ex_changed
assert ex<=4,ex
pub=json.loads((O/'E0_publish.json').read_text())
with open(pub['path'],'rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
assert h==pub['sha256'];rep['published_sha256_after_reopen']=h
(O/'E3_final_readback.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep),flush=True)
