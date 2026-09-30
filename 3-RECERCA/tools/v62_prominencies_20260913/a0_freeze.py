from pathlib import Path
import sys,json,hashlib,gc
import numpy as np
from psd_tools import PSDImage
from psd_tools.constants import Tag,Resource
R=Path('/Users/USUARI/Downloads/Eclipse 2026');O=R/'output/v62_prominencies_20260913'
sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'))
from common60 import chan,box,sha
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V62_V61_PROMINENCES_20260913'
p=O/'V61_Pere_input.psb';s=PSDImage.open(p);rows=[]
for i,l in enumerate(s):
 row=dict(index=i,name=l.name,id=int(l._record.tagged_blocks.get_data(Tag.LAYER_ID)),bbox=l.bbox,kind=l.kind,visible=l.visible,opacity=l.opacity,blend=str(l.blend_mode),channels=[dict(id=int(q.id),sha256=hashlib.sha256(c.data).hexdigest()) for q,c in zip(l._record.channel_info,l._channels)])
 if l.kind=='smartobject':row['transform']=list(l.smart_object.transform_box)
 for q in l._record.channel_info:
  c=int(q.id)
  if i<3 or i>17 or l.kind=='smartobject' or c in [-1,-2,1]:np.save(O/'arrays'/f'V61_L{i:02d}_C{c}.npy',box(l,c))
 rows.append(row);print(row,flush=True);gc.collect()
h=sha(p);src=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V61.psb');assert sha(src)==h
(O/'AdobeRGB.icc').write_bytes(s._record.image_resources[Resource.ICC_PROFILE].data)
(O/'A0_sources.json').write_text(json.dumps(dict(path=str(src),snapshot=str(p),sha256=h,bytes=p.stat().st_size,size=s.size,depth=s.depth,layers=rows),indent=2,ensure_ascii=False))
