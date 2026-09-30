from common58 import *
import sys,gc
from scipy.ndimage import distance_transform_edt,maximum_filter,gaussian_filter
from psd_tools import PSDImage
from psd_tools.psd.layer_and_mask import ChannelData
from psd_tools.constants import Compression
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
claim();s=PSDImage.open(O/'V58.psb');moon=roi(29,-2).astype(float)/65535;dist=distance_transform_edt(moon==0);# measured contour, not a solar-centered replacement circle
# User-requested RHEF protection: opaque exclusion through4px beyond the actual feather, smooth transition to full strength by12px.
w=np.clip((dist-4)/8,0,1);w=w*w*(3-2*w)
# Photometric prominence protection uses the already existing accepted source criterion R-G>0.25 (S5).
red=np.load(O/'arrays/L10_C0_roi.npy').astype(float)/65535;green=roi(10).astype(float)/65535;prom=red-green>.25;pm=maximum_filter(prom.astype('float32'),size=9);pm=np.clip(gaussian_filter(pm,2),0,1);w*=1-pm
# Freeze this editable display selection. Filter pixels and photographic bases are untouched.
np.save(O/'prepared_layers/RHEF_protection_weight.npy',w.astype('float32'));rep={'scope':'User-requested enlargement of RHEF masks and protection of real pearls/prominences; editable display selection, no source/raster correction','contour':'actual V56 lunar feather; no circle/radius fit','margin_and_transition_px':[4,12],'prominence_criterion':'accepted S5 red-green>0.25,9pxdilation andsigma2edge','raster_changed':False,'layers':{}}
expected=dict(json.loads((O/'G6_package.json').read_text())['edited_channel_raw_sha256'])
for idx in [13,14,15,16]:
 l=s[idx];a=chan(l,-2).copy();v=a[2777:4777,4377:6377];v[:]=np.round(v*w).astype('uint16');ci=next(i for i,q in enumerate(l._record.channel_info) if int(q.id)==-2);cd=ChannelData(Compression.ZIP);cd.set_data(a.astype('>u2').tobytes(),10551,7506,16,2);l._channels[ci]=cd;l._record.channel_info[ci].length=len(cd.data)+2;expected[f'{idx}:-2']=hashlib.sha256(a.astype('>u2').tobytes()).hexdigest();rep['layers'][str(idx)]=dict(fully_protected_prominence_pixels=int(np.sum(prom&(v<100))),measured_prominence_pixels=int(prom.sum()),source_channels_unchanged=True)
finalize_lr16(s);s._updated=False;p=O/'V58_protected_work.psb';assert not p.exists()
with p.open('xb') as f:s.save(f)
rep['path']=str(p);rep['edited_channel_raw_sha256']=expected;save('G9_RHEF_protection.json',rep);print('PROTECTED_WRITTEN',flush=True)
