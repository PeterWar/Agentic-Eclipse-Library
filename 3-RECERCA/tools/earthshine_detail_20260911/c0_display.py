"""Fixed photographic frequency composition before CameraRaw.
Preserve the user's existing coarse tone/texture. Replace only fixed fine frequencies with the observed corrected source; no spatial
mask, radius, painted marks or external texture enters this operation.
This is a photographic delta, not a replacement scientific radiance estimate.
"""
from detail_common import *
import sys
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from c5_fonts_psb import C,PSDImage,fingerprint
from psd_tools.constants import Tag,Resource
z=np.load(OUT/'B1_full_native_ensemble.npz');old=np.load(ROOT/'research/tools/v46_earthshine_20260911/cau/live_lunar_rgb_u16.npy').astype(float)/65535
t=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F7_fonts.json').read_text())['tone']
def inv(u):return t['mid']+t['soft']*np.sinh((u-t['anchor'])/t['scale'])
def display(g):return t['anchor']+t['scale']*np.arcsinh((g-t['mid'])/t['soft'])
from scipy.fft import dctn,idctn
# Fixed 8-16px crossover already used by the source compositor. Retain the
# user's coarse photographic structure, replace legacy fine frequencies with
# observed source frequencies over the whole rectangle before CameraRaw.
freq=np.hypot((np.arange(N)/(2*N))[:,None],(np.arange(N)/(2*N))[None,:]);tt=np.clip((freq-1/16)/(1/8-1/16),0,1);H=.5-.5*np.cos(np.pi*tt)
source_display=display(z['candidate']);legacy=old.mean(-1)
newmono=legacy+idctn(dctn(source_display-legacy,type=2,norm='ortho')*H,type=2,norm='ortho')
u=old+(newmono-legacy)[...,None]
assert np.all(np.isfinite(u)) and u.min()>0 and u.max()<1
rgb=np.rint(u*65535).astype(np.uint16);np.save(OUT/'C0_pre_camera_raw_rgb.npy',rgb)
s=PSDImage.open(ROOT/'research/tools/v46_earthshine_20260911/V45_live_source.psd')
name='V45 font G · dos trens · preferència temporal · vel present';l=next(l for l in s if l.name==name);before=fingerprint(l)
for info,channel in zip(l._record.channel_info,l._channels):
 if int(info.id) in [0,1,2]:
  c=int(info.id);channel.set_data(np.ascontiguousarray(rgb[...,c].astype('>u2')).tobytes(),1400,1400,16,1);info.length=len(channel.data)+2
C.finalize_lr16(s);s._updated=False
p=OUT/'C0_pre_camera_raw_full.psd';assert not p.exists()
with p.open('xb') as f:s.save(f)
save('C0_pre_camera_raw.json',dict(method=__doc__,source_layer=before,tone=t,source_delta='Fixed 8-16px Cartesian frequency replacement before CameraRaw; old coarse photographic structure plus corrected source fine frequencies',output=str(p),minmax_u16=[int(rgb.min()),int(rgb.max())],source_only_Vixen=True,science_radiance_claim=False))
print('PREPARED',p,flush=True)
