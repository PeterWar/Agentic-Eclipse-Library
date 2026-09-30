"""Extract original V42 photographic channels before the Earthshine09 flatten.
Pure diagnostic; originals opened read-only and all writes in current namespace.
"""
from common50 import *
import sys,gc
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from inspect_inputs import channel
from psd_tools import PSDImage
src=Path(json.loads((ROOT/'output/v42_20260910/4-rebuts/C4_publish.json').read_text())['path'])
print('OPEN',src,flush=True);s=PSDImage.open(src);rows=[]
for l in s:
 if l.name[:2] not in ['09','10','11','12']:continue
 key=l.name[:2];bb=l.bbox;ys=slice(Y0-bb[1],Y0-bb[1]+N);xs=slice(X0-bb[0],X0-bb[0]+N)
 rgb=np.stack([channel(l,c)[ys,xs] for c in range(3)],-1);a=channel(l,-1);a=np.full((N,N),65535,np.uint16) if a is None else a[ys,xs].copy()
 md=l._record.mask_data;mask=np.full((N,N),65535,np.uint16) if md is None else channel(l,-2)[Y0-md.top:Y0-md.top+N,X0-md.left:X0-md.left+N].copy()
 np.savez_compressed(OUT/f'L4_original_{key}.npz',rgb=rgb,alpha=a,mask=mask)
 rows.append(dict(name=l.name,bbox=list(bb),visible=l.visible,opacity=l.opacity,blend=str(l.blend_mode),mask_bbox=None if md is None else [md.left,md.top,md.right,md.bottom],mask_flags=None if md is None else str(md.flags)))
 print(rows[-1],flush=True);del rgb,a,mask;gc.collect()
save('L4_original_solar_layers.json',dict(source=str(src),layers=rows));print('DONE',flush=True)
