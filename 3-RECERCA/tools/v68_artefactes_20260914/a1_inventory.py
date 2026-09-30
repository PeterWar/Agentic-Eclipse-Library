from pathlib import Path
import json,sys,hashlib,gc
import numpy as np
from psd_tools import PSDImage
from psd_tools.constants import Tag,Resource
R=Path.cwd();O=R/'output/v68_artefactes_20260914';sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V68_V67_ARTIFACTS_20260914'
f=O/'V67_Pere_input.psb'
with f.open('rb') as h: sha=hashlib.file_digest(h,'sha256').hexdigest()
p=PSDImage.open(f);rows=[]
for i,l in enumerate(p):
 lid=int(l._record.tagged_blocks.get_data(Tag.LAYER_ID));m=l._record.mask_data
 q=dict(index=i,id=lid,name=l.name,kind=l.kind,bbox=l.bbox,visible=l.visible,opacity=l.opacity,blend=str(l.blend_mode),channels=[int(c.id) for c in l._record.channel_info])
 if m:q['mask']=dict(bbox=[m.left,m.top,m.right,m.bottom],background=m.background_color,disabled=m.flags.mask_disabled)
 if l.kind=='smartobject':q['transform']=list(l.smart_object.transform_box)
 rows.append(q);print(json.dumps(q,ensure_ascii=False),flush=True)
 if i>=len(p)-2:
  for c in l._record.channel_info:np.save(O/'arrays'/f'A1_L{lid}_C{int(c.id)}.npy',chan(l,int(c.id)))
 gc.collect()
(O/'AdobeRGB.icc').write_bytes(p._record.image_resources[Resource.ICC_PROFILE].data)
(O/'A1_layers.json').write_text(json.dumps(dict(source=str(f),sha256=sha,size=p.size,depth=p.depth,layers=rows),ensure_ascii=False,indent=2)+'\n')
