from pathlib import Path
import json,hashlib,sys,gc
import numpy as np
from psd_tools import PSDImage
from psd_tools.constants import Tag,Resource
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan,box
p=PSDImage.open(O/'V64_Pere_input.psb');rows=[]
for i,l in enumerate(p):
 lid=int(l._record.tagged_blocks.get_data(Tag.LAYER_ID));m=l._record.mask_data;q=dict(index=i,id=lid,name=l.name,kind=l.kind,bbox=l.bbox,visible=l.visible,opacity=l.opacity,blend=str(l.blend_mode))
 if m:q['mask']=dict(bbox=[m.left,m.top,m.right,m.bottom],background=m.background_color,disabled=m.flags.mask_disabled)
 if l.kind=='smartobject':q['transform']=list(l.smart_object.transform_box)
 if lid in [3,30,76,83,87] or i>=len(p)-5:
  for c in l._record.channel_info:np.save(A/f'L{lid}_C{int(c.id)}.npy',box(l,int(c.id)))
 rows.append(q);print(json.dumps(q,ensure_ascii=False),flush=True);gc.collect()
(O/'AdobeRGB.icc').write_bytes(p._record.image_resources[Resource.ICC_PROFILE].data)
(O/'A1_layers.json').write_text(json.dumps(dict(size=p.size,depth=p.depth,layers=rows),ensure_ascii=False,indent=2)+'\n')
