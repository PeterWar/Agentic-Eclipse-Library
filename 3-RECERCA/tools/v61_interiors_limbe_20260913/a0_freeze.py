from common61 import *
import subprocess,attrs,gc
from psd_tools import PSDImage
from psd_tools.constants import Resource
claim();manifest={}
for key,p in [('V60',SRC),('Vista',REF),('V57',V57)]:
 stamp=p.stat();h=sha(p)
 if key!='V57':
  dst=O/(key+'_Pere_input.psb');assert not dst.exists();subprocess.run(['/bin/cp','-c',str(p),str(dst)],check=True);assert sha(dst)==h
 else:dst=p
 assert p.stat().st_mtime_ns==stamp.st_mtime_ns
 s=PSDImage.open(dst);rows=[]
 for i,l in enumerate(s):
  m=l._record.mask_data;rows.append(dict(index=i,name=l.name,bbox=l.bbox,blend=str(l.blend_mode),opacity=l.opacity,visible=l.visible,mask=m.tobytes().hex() if m else None,mask_flags=attrs.asdict(m.flags) if m else None,channels=[dict(id=int(ci.id),sha256=hashlib.sha256(cd.data).hexdigest(),compression=int(cd.compression)) for ci,cd in zip(l._record.channel_info,l._channels)]))
  if key=='V60' or (key=='V57' and i<11) or key=='Vista':
   for ci in l._record.channel_info:
    c=int(ci.id)
    if key=='V60' and 11<=i<=26 and c in [0,2]:continue
    np.save(O/'arrays'/f'{key}_L{i:02d}_C{c}.npy',box(l,c))
  print(key,i,l.name,l.visible,l.opacity,l.bbox,flush=True)
 manifest[key]=dict(path=str(p),snapshot=str(dst),sha256=h,bytes=stamp.st_size,layers=rows,size=s.size,depth=s.depth)
 if key=='V60':(O/'AdobeRGB.icc').write_bytes(s._record.image_resources[Resource.ICC_PROFILE].data)
 del s;gc.collect()
save('A0_sources.json',manifest)
