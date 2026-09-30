from common60 import *
import shutil,attrs,datetime,gc
from psd_tools import PSDImage
from psd_tools.constants import Resource
from PIL import Image,ImageCms
import io
claim();stamp=SRC.stat();source_sha=sha(SRC);dst=O/'V59_Pere_input.psb';assert not dst.exists()
with SRC.open('rb') as fi,dst.open('xb') as fo:shutil.copyfileobj(fi,fo,16*1024*1024)
assert sha(dst)==source_sha and SRC.stat().st_mtime_ns==stamp.st_mtime_ns
s=PSDImage.open(dst);assert len(s)==31 and s.size==(10551,7506) and s.depth==16;D=O/'arrays';D.mkdir();V=O/'vistes';V.mkdir();rows=[]
for i,l in enumerate(s):
 m=l._record.mask_data;row=dict(index=i,name=l.name,bbox=l.bbox,blend=str(l.blend_mode),opacity=l.opacity,visible=l.visible,mask=m.tobytes().hex() if m else None,mask_flags=attrs.asdict(m.flags) if m else None,channels=[])
 for ci,cd in zip(l._record.channel_info,l._channels):row['channels'].append(dict(id=int(ci.id),compression=int(cd.compression),sha256=hashlib.sha256(cd.data).hexdigest()))
 rows.append(row);print(i,l.name,l.visible,l.opacity,str(l.blend_mode),flush=True)
 for c in [1,-1,-2]+([0,2] if i in [0,1,9,10,29,30] else []):
  if not any(int(q.id)==c for q in l._record.channel_info):continue
  a=box(l,c);np.save(D/f'L{i:02d}_C{c}_roi.npy',a)
  if i==30:np.save(D/f'MARK_C{c}.npy',chan(l,c))
 del a;gc.collect()
m=s[30];rgb=np.stack([chan(m,c) for c in range(3)],-1);al=chan(m,-1);np.save(D/'MARK_RGB.npy',rgb);np.save(D/'MARK_ALPHA.npy',al);np.save(D/'MARK_BBOX.npy',m.bbox)
icc=s._record.image_resources[Resource.ICC_PROFILE].data;(O/'AdobeRGB.icc').write_bytes(icc);save('A0_freeze.json',dict(source=str(SRC),snapshot=str(dst),sha256=source_sha,bytes=stamp.st_size,time=datetime.datetime.now(datetime.timezone.utc).isoformat(),layers=rows,size=s.size,depth=s.depth,icc_sha256=hashlib.sha256(icc).hexdigest(),native_source_saved=True,mark_bbox=m.bbox));print('FROZEN',flush=True)
