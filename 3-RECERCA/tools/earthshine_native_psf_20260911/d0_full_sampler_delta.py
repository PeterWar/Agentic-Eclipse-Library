"""Transfer the full measured source interpolation delta before CameraRaw.
Previous V48 photographic pre-CR source plus display(new physical sampler)
minus display(old physical sampler). No frequency truncation of this correction,
no painted selection, no radial mask or retuned tone. The inherited photographic
base remains; this is not an absolute scientific radiance replacement.
"""
from full_delta_common import *
import sys
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from c5_fonts_psb import C,PSDImage,fingerprint
tone=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F7_fonts.json').read_text())['tone']
def display(g):return tone['anchor']+tone['scale']*np.arcsinh((g-tone['mid'])/tone['soft'])
oldsource=np.load(SRC/'B1_full_native_ensemble.npz')['candidate'];newsource=np.load(PARENT/'B0_new_all.npz')['candidate'];baseline=np.load(SRC/'C0_pre_camera_raw_rgb.npy').astype(float)
delta=display(newsource)-display(oldsource);rgb=baseline+delta[...,None]*65535
assert np.isfinite(rgb).all() and rgb.min()>0 and rgb.max()<65535
rgb=np.rint(rgb).astype(np.uint16);np.save(OUT/'C0_pre_camera_raw_rgb.npy',rgb)
s=PSDImage.open(ROOT/'research/tools/v46_earthshine_20260911/V45_live_source.psd');l=next(l for l in s if l.name=='V45 font G · dos trens · preferència temporal · vel present');before=fingerprint(l)
for info,ch in zip(l._record.channel_info,l._channels):
    if int(info.id) in [0,1,2]:
        c=int(info.id);ch.set_data(np.ascontiguousarray(rgb[...,c].astype('>u2')).tobytes(),1400,1400,16,1);info.length=len(ch.data)+2
C.finalize_lr16(s);s._updated=False;dst=OUT/'C0_pre_camera_raw_full.psd';assert not dst.exists()
with dst.open('xb') as f:s.save(f)
save('C0_pre_camera_raw.json',dict(method=__doc__,tone=tone,source_layer=before,output=str(dst),delta_minmax_DN16=[float(delta.min()*65535),float(delta.max()*65535)],minmax_u16=[int(rgb.min()),int(rgb.max())],source_only_delta_Vixen=True,source_calibration_geometry_frozen=True,spatial_mask=False,frequency_selection=False))
print('PREPARED',dst,flush=True)
