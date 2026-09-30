from pathlib import Path
import sys,json,numpy as np,gc
from psd_tools import PSDImage
from psd_tools.constants import Tag,Compression
from psd_tools.psd.layer_and_mask import ChannelData
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V65_PERE_GEOMETRY_STARS_20260914';p=PSDImage.open(O/'D0_pilot_source.psb');assert p.size==(2000,2000);rep=[]
for l in p:
 lid=int(l._record.tagged_blocks.get_data(Tag.LAYER_ID))
 if lid not in [3,76]:continue
 new=np.load(A/('B11_base_k0.9.npy' if lid==3 else 'B10_L76_colour.npy'));x0,y0,x1,y1=max(l.left,0),max(l.top,0),min(l.right,2000),min(l.bottom,2000)
 for c in range(3):
  a=chan(l,c).copy();a[y0-l.top:y1-l.top,x0-l.left:x1-l.left]=new[y0:y1,x0:x1,c];i=next(i for i,v in enumerate(l._record.channel_info) if int(v.id)==c);cd=ChannelData(Compression.ZIP);cd.set_data(a.astype('>u2').tobytes(),l.width,l.height,16,2);l._channels[i]=cd;l._record.channel_info[i].length=len(cd.data)+2
 rep.append(dict(id=lid,bbox=l.bbox))
finalize_lr16(p);p._updated=False;dst=O/'D4_artifact_pilot.psb';assert not dst.exists()
with dst.open('xb') as f:p.save(f)
print('BUILT',rep)
