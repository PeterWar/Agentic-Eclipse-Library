from common58 import *
from psd_tools import PSDImage
from psd_tools.psd.layer_and_mask import ChannelData
from psd_tools.constants import Compression
import sys
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
claim();s=PSDImage.open(O/'V58_enabled_work.psb');w=np.load(O/'prepared_layers/RHEF_protection_weight.npy');exp=json.loads((O/'G9_RHEF_protection.json').read_text())['edited_channel_raw_sha256'];rep={'reason':'Native100% review H7 also exposes NRGF inversion of real pearls/prominences. Apply the same editable display protection already validated for RHEF; source filter raster and Earthshine unchanged.','layers':{}}
for idx in [11,12]:
 l=s[idx];a=chan(l,-2).copy();v=a[2777:4777,4377:6377];v[:]=np.round(v*w).astype('uint16');i=next(i for i,q in enumerate(l._record.channel_info) if int(q.id)==-2);cd=ChannelData(Compression.ZIP);cd.set_data(a.astype('>u2').tobytes(),10551,7506,16,2);l._channels[i]=cd;l._record.channel_info[i].length=len(cd.data)+2;exp[f'{idx}:-2']=hashlib.sha256(a.astype('>u2').tobytes()).hexdigest();rep['layers'][str(idx)]={'mask_enabled':not l._record.mask_data.flags.mask_disabled,'raster_unchanged':True}
finalize_lr16(s);s._updated=False;p=O/'V58_reviewed_work.psb';assert not p.exists()
with p.open('xb') as f:s.save(f)
rep['path']=str(p);rep['expected_channels']=exp;save('I0_NRGF_protection.json',rep);print('NRGF_PROTECTED',flush=True)
