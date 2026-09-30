from common58 import *
import sys,gc
from psd_tools import PSDImage
from psd_tools.psd.layer_and_mask import ChannelData
from psd_tools.constants import Compression
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
claim();s=PSDImage.open(O/'V58_work.psb');M9=roi(9,-2);moon=roi(29,-2);rep={'reason':'Normal alpha compositing: complementary masks applied once to underlay and again by overlying Moon produce squared transition and black/bright edge. Use accepted V56 base underlap instead. No change to Moon image or alpha.'};expected=dict(json.loads((O/'G1_assembly.json').read_text())['edited_channel_raw_sha256'])
def put(l,c,a):
 i=next(i for i,q in enumerate(l._record.channel_info) if int(q.id)==c);cd=ChannelData(Compression.ZIP);h,w=a.shape;cd.set_data(a.astype('>u2').tobytes(),w,h,16,2);l._channels[i]=cd;l._record.channel_info[i].length=len(cd.data)+2;return hashlib.sha256(a.astype('>u2').tobytes()).hexdigest()
for idx in [1]+list(range(11,27)):
 l=s[idx];a=chan(l,-2).copy();md=l._record.mask_data;xa,ya,xb,yb=ROI;v=a[ya-md.top:yb-md.top,xa-md.left:xb-md.left]
 if idx==1:
  y,x=np.ogrid[ya:yb,xa:xb];r=np.hypot(x-5376.5681,y-3776.6475);w=np.clip((480-r)/15,0,1);w=w*w*(3-2*w);v[:]=np.round(v*(1-w)+M9*w).astype('uint16')
 else:
  # Preserve the exact operator support while replacing only the lunar occlusion rule.
  name={15:'P02c_RHEF_local60_native',16:'P02d_RHEF_local30_native'}.get(idx);sup=np.load(O/'filters'/f'{name}_support.npy',mmap_mode='r')[ya:yb,xa:xb] if name else np.load(O/'filters/angular_support.npy',mmap_mode='r')[ya:yb,xa:xb] if idx in [17,18,19] else np.load(O/'sources/support.npy',mmap_mode='r')[ya:yb,xa:xb];v[:]=np.where(sup,M9,0)
 expected[f'{idx}:-2']=put(l,-2,a);edge=(moon>6553)&(moon<58981);rep[str(idx)]=dict(edge_underlay_mask_quantiles=np.percentile(v[edge],[0,10,50,90,100]).tolist(),fully_occulted_leak_max=int(v[(moon==65535)&(M9==0)].max()),operator_gap_pixels=int(np.sum(edge&(v==0))));print(idx,rep[str(idx)],flush=True)
finalize_lr16(s);s._updated=False;p=O/'V58_overlap_work.psb';assert not p.exists()
with p.open('xb') as f:s.save(f)
rep['edited_channel_raw_sha256']=expected;rep['path']=str(p);save('G4_overlap_correction.json',rep);print('OVERLAP_WRITTEN',flush=True)
