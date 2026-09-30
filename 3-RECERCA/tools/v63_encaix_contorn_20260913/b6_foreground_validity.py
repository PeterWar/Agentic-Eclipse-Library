from pathlib import Path
import sys,json,numpy as np,tifffile as tf
from scipy.ndimage import label,binary_dilation,gaussian_filter
from psd_tools import PSDImage
from psd_tools.constants import Compression,Resource,Tag
from psd_tools.psd.layer_and_mask import ChannelData
R=Path.cwd();O=R/'output/v63_encaix_contorn_20260913';P=R/'output/v62_prominencies_20260913';A=O/'arrays'
sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V63_INNER_ALIGNMENT_LUNAR_CONTOUR_20260913'
rgb=tf.imread(R/'output/v61_interiors_limbe_20260913/V61_interiors_only.tif').astype('float32')/65535
mx=rgb.max(-1);labs,_=label(mx<.05);core=labs==labs[1000,1000];valid=~binary_dilation(core,iterations=5);den=gaussian_filter(valid.astype('float32'),8)
old=np.load(P/'arrays/C2_matte_alpha16_local.npy');support=np.minimum(den/1e-8,1);new=np.rint(old.astype('float64')*support).astype('uint16')
bright=(mx>=.05);assert np.array_equal(old[bright],new[bright]);assert np.all(new<=old)
np.save(A/'B6_foreground_alpha.npy',new);np.save(A/'B6_support.npy',support)
rep=dict(method='Restrict old C2 coverage to the validity of its continuum denominator. Use its existing 1e-8 floor as support limit; no new lunar contour or radius.',changed=int(np.count_nonzero(old!=new)),continuum_invalid=int(np.count_nonzero(den<1e-8)),all_source_pixels_maxRGB_at_least_point05_exact=bool(np.array_equal(old[bright],new[bright])),foreground_sample_count=int(bright.sum()),source_background_RGB_max=float(mx[den<1e-8].max()),original_7_layers_edited=False,limit='The old whole-black-photo reconstruction identity does not apply in invalid dark lunar background; genuine solar foreground is retained.')
s=PSDImage.open(P/'Interiors_V62_editables.psb');g=s[0];md=g._record.mask_data;arr=chan(g,-2).copy();x0,y0=max(md.left,3480),max(md.top,2365);x1,y1=min(md.right,5480),min(md.bottom,4365);arr[y0-md.top:y1-md.top,x0-md.left:x1-md.left]=new[y0-2365:y1-2365,x0-3480:x1-3480]
# The old trimmed rectangle must contain all non-white coverage, including the repair.
check=np.full(new.shape,65535,np.uint16);check[y0-2365:y1-2365,x0-3480:x1-3480]=arr[y0-md.top:y1-md.top,x0-md.left:x1-md.left];assert np.array_equal(check,new)
i=next(i for i,c in enumerate(g._record.channel_info) if int(c.id)==-2);cd=ChannelData(Compression.ZIP);cd.set_data(arr.astype('>u2').tobytes(),arr.shape[1],arr.shape[0],16,2);g._channels[i]=cd;g._record.channel_info[i].length=len(cd.data)+2;g.name='Interiors V57 · fons negre amb suport vàlid V63'
finalize_lr16(s);s._updated=False;p=O/'Interiors_V63_validity.psb';assert not p.exists()
with p.open('xb') as f:s.save(f)
(O/'B6_foreground_validity.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep),flush=True)
