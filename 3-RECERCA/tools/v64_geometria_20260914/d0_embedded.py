from pathlib import Path
import io,json,sys,hashlib
import numpy as np
from psd_tools import PSDImage
from psd_tools.constants import Tag,Compression
from psd_tools.psd.layer_and_mask import ChannelData
R=Path.cwd();O=R/'output/v64_geometria_20260914';A=O/'arrays'
sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V64_V63_GREEN_GEOMETRY_20260914'
p=PSDImage.open(O/'V63_Pere_input.psb');so=next(l for l in p if int(l._record.tagged_blocks.get_data(Tag.LAYER_ID))==76);data=so.smart_object.data
z=O/'Interiors_Pere_embedded_input.psb'
if z.exists():assert z.read_bytes()==data
else:z.write_bytes(data)
s=PSDImage.open(io.BytesIO(data));g=s[0]
assert g.is_group() and len(g)==8
new=np.load(A/'B6_alpha_source.npy');md=g._record.mask_data;arr=chan(g,-2).copy();before=arr.copy();x0,y0=max(md.left,3480),max(md.top,2365);x1,y1=min(md.right,5480),min(md.bottom,4365)
native_old=np.full(new.shape,65535,np.uint16);native_old[y0-2365:y1-2365,x0-3480:x1-3480]=arr[y0-md.top:y1-md.top,x0-md.left:x1-md.left]
new=np.maximum(new,native_old);np.save(A/'D0_native_expected_mask.npy',new)
arr[y0-md.top:y1-md.top,x0-md.left:x1-md.left]=new[y0-2365:y1-2365,x0-3480:x1-3480]
check=np.full(new.shape,65535,np.uint16);check[y0-2365:y1-2365,x0-3480:x1-3480]=arr[y0-md.top:y1-md.top,x0-md.left:x1-md.left];assert np.array_equal(check,new)
i=next(i for i,c in enumerate(g._record.channel_info) if int(c.id)==-2);cd=ChannelData(Compression.ZIP);cd.set_data(arr.astype('>u2').tobytes(),arr.shape[1],arr.shape[0],16,2);g._channels[i]=cd;g._record.channel_info[i].length=len(cd.data)+2;g.name='Interiors V57 · cobertura per exposició · V64'
finalize_lr16(s);s._updated=False;dst=O/'Interiors_V64_exposure_monotone.psb';assert not dst.exists()
with dst.open('xb') as f:s.save(f)
(O/'D0_embedded_monotone.json').write_text(json.dumps(dict(source_embedded_sha256=hashlib.sha256(data).hexdigest(),source_parent=str(O/'V63_Pere_input.psb'),changed_mask_pixels=int(np.count_nonzero(arr!=before)),pixels_with_increased_coverage=int(np.count_nonzero(arr>before)),pixels_with_reduced_coverage=int(np.count_nonzero(arr<before)),quantization_note='Retain native original when the serialized producer value was lower by 1 DN16; no opacity reductions.',group_children=len(g),source_transform=list(so.smart_object.transform_box)),indent=2)+'\n');print('BUILT',dst,flush=True)
