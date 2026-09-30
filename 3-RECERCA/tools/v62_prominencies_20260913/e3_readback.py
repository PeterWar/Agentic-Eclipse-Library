from pathlib import Path
import json,numpy as np,tifffile as tf
O=Path('output/v62_prominencies_20260913')
assert 'FINAL_OPEN_COMPLETE' in (O/'E2_final_open.log').read_text()
a=tf.imread(O/'V62_candidate.tif');b=tf.imread(O/'V62_final_readback.tif');assert a.shape==b.shape==(7506,10551,4)
mx=0;nonzero=0;sumdiff=0
for y in range(0,a.shape[0],128):
 d=abs(a[y:y+128].astype('int32')-b[y:y+128].astype('int32'));mx=max(mx,int(d.max()));nonzero+=int(np.count_nonzero(d));sumdiff+=int(d.sum())
assert mx<=4,mx
p=O/'E3_final_readback.json';assert not p.exists();p.write_text(json.dumps(dict(PASS=True,shape=list(a.shape),max_DN16=mx,nonzero_channel_values=nonzero,mean_DN16=sumdiff/a.size,scope='All canvas RGBA: native candidate compared with reopened published PSB and forced recomposition in a disposable full-layer duplicate'),indent=2)+'\n')
print('FULL CANVAS READBACK PASS',mx,nonzero,flush=True)
