from pathlib import Path
import hashlib,json,gc
import numpy as np,tifffile as tf
from psd_tools import PSDImage
from psd_tools.psd.image_data import ImageData
from psd_tools.constants import Compression
R=Path('/Users/USUARI/Downloads/Eclipse 2026');O=R/'output/v57_integracio_20260913'
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_CAPES_TOTALS_V57_20260913'

def fp(l):
 return dict(name=l.name,bbox=list(l.bbox),opacity=l.opacity,blend=str(l.blend_mode),visible=l.visible,
  channels=[dict(id=int(ci.id),compression=int(cd.compression),sha256=hashlib.sha256(cd.data).hexdigest()) for ci,cd in zip(l._record.channel_info,l._channels)],
  mask=None if l._record.mask_data is None else l._record.mask_data.tobytes().hex())
expected=json.loads((O/'B0_assembly.json').read_text())['expected']
s=PSDImage.open(O/'V57_work.psb');assert len(s)==35 and s.size==(10551,7506) and s.depth==16
assert [fp(l) for l in s]==expected
s[10].visible=False
expected[10]['visible']=False
# Keep the imported prominence composite as an alternative. The V42 prominence
# stack remains active, so the corona outside the lunar neighbourhood is exact.
import sys
sys.path.insert(0,str(R/'research/tools/encaix_sony'))
from psb_utils import finalize_lr16
finalize_lr16(s)
assert s._record.header.channels==3
arr=tf.imread(O/'V57_noSolar_native.tif');assert arr.shape==(7506,10551,3) and arr.dtype==np.uint16
im=ImageData(compression=Compression.RAW)
im.set_data([np.ascontiguousarray(arr[...,i].astype('>u2')).tobytes() for i in range(3)],s._record.header)
s._record.image_data=im;s._updated=False
target=O/'V57.psb';assert not target.exists()
with target.open('xb') as f:s.save(f)
del s,im;gc.collect()
s=PSDImage.open(target);assert [fp(l) for l in s]==expected
channels=s._record.image_data.get_data(s._record.header)
mx=0
for i,c in enumerate(channels):
 ref=np.frombuffer(c,dtype='>u2').reshape(7506,10551)
 mx=max(mx,int(np.max(np.abs(ref.astype('int32')-arr[...,i].astype('int32')))))
assert mx==0
with target.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
rep=dict(PASS=True,path=str(target),sha256=sha,bytes=target.stat().st_size,layers=35,size=[10551,7506],depth=16,
 original_layers_preserved=32,original_channels_masks_geometry_exact=True,imported_V56_layers_exact=3,
 expected_fingerprints_match=True,merged_cache_native_max_DN16=mx,profile='Adobe RGB (1998)',geometry='identity; no resampling')
(O/'D0_expected_layers.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2))
(O/'D0_package.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep),flush=True)
