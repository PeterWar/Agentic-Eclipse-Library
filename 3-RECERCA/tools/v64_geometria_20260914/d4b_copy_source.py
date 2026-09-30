from pathlib import Path
import sys,json,copy
from psd_tools import PSDImage
from psd_tools.constants import Tag
R=Path.cwd();O=R/'output/v64_geometria_20260914'
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
p=PSDImage.open(O/'V63_Pere_input.psb');l=next(l for l in p if int(l._record.tagged_blocks.get_data(Tag.LAYER_ID))==83)
for q in list(p):
 if q is not l:p.remove(q)
x,y,x1,y1=l.bbox;r=l._record;r.left-=x;r.right-=x;r.top-=y;r.bottom-=y
m=r.mask_data;m.left-=x;m.right-=x;m.top-=y;m.bottom-=y
p._record.header.width=x1-x;p._record.header.height=y1-y
for k in list(p._record.layer_and_mask_information.tagged_blocks.keys()):
 if bytes(k).startswith(b'lnk'):del p._record.layer_and_mask_information.tagged_blocks[k]
finalize_lr16(p);p._updated=False;dst=O/'Copy12_V64_original_editable.psb';assert not dst.exists();p.save(dst)
print(dst,p.size,l.bbox,(m.left,m.top,m.right,m.bottom),flush=True)
