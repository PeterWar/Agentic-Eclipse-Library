from pathlib import Path
import sys,json,hashlib,gc
import numpy as np
from psd_tools import PSDImage
from psd_tools.constants import Tag,Resource
R=Path.cwd();O=R/'output/v64_geometria_20260914';A=O/'arrays';A.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'))
from common60 import chan,box,sha
p=O/'V63_disk_input.psb';s=PSDImage.open(p);rows=[]
for i,l in enumerate(s):
    lid=int(l._record.tagged_blocks.get_data(Tag.LAYER_ID));md=l._record.mask_data
    q=dict(index=i,id=lid,name=l.name,visible=l.visible,opacity=l.opacity,bbox=l.bbox,kind=l.kind,blend=str(l.blend_mode))
    if md:q['mask']=dict(bbox=[md.left,md.top,md.right,md.bottom],background=md.background_color,disabled=md.flags.mask_disabled)
    if l.kind=='smartobject':q['transform']=list(l.smart_object.transform_box)
    if lid in [3,30,76,83,87]:
        for ci in l._record.channel_info:np.save(A/f'L{lid}_C{int(ci.id)}.npy',box(l,int(ci.id)))
    rows.append(q);print(q,flush=True);gc.collect()
(O/'AdobeRGB.icc').write_bytes(s._record.image_resources[Resource.ICC_PROFILE].data)
h=sha(p);(O/'A1_sources.json').write_text(json.dumps(dict(path=str(p),sha256=h,bytes=p.stat().st_size,layers=rows),ensure_ascii=False,indent=2)+'\n')
print('COMPLETE',h,flush=True)
