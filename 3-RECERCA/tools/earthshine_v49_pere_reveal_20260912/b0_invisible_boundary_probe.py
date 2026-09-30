"""Causal Camera Raw probe: alter only pixels invisible in the inherited mask.
No modified input pixel can enter the composite. This is an auxiliary boundary
test of the historical CR operator, not a new astronomical source or a replay
of the user's newly baked and unknown exact slider settings.
"""
from reveal_common import *
from scipy.ndimage import distance_transform_edt
from psd_tools import PSDImage
from psd_tools.constants import Tag
from psd_tools.psd.layer_and_mask import LayerInfo
BASE=ROOT/'output/earthshine_native_psf_20260911/full_sampler_delta'
src=BASE/'C0_pre_camera_raw_full.psd';target=OUT/'B0_auxiliary_boundary_input.psd';assert not target.exists()
mask=np.load(OUT/'A0_inherited_mask_roi.npy');known=mask>0;rgb=np.load(BASE/'C0_pre_camera_raw_rgb.npy');assert rgb.shape==(N,N,3)
indices=distance_transform_edt(~known,return_distances=False,return_indices=True);aux=rgb.copy();aux[~known]=rgb[indices[0][~known],indices[1][~known]]
assert np.array_equal(aux[known],rgb[known]);np.save(OUT/'B0_auxiliary_input_RGB16.npy',aux)
s=PSDImage.open(src);l=next(l for l in s if l.name=='V45 font G · dos trens · preferència temporal · vel present')
assert np.array_equal(np.stack([channel(l,c) for c in range(3)],-1),rgb)
for ci,cd in zip(l._record.channel_info,l._channels):
    if int(ci.id) in [0,1,2]:cd.set_data(np.ascontiguousarray(aux[...,int(ci.id)].astype('>u2')).tobytes(),N,N,16,s.version);ci.length=len(cd.data)+2
s._update_record();lm=s._record.layer_and_mask_information;li=lm.layer_info;lm.tagged_blocks.set_data(Tag.LAYER_16,li.layer_count,li.layer_records,li.channel_image_data);lm.layer_info=LayerInfo();s._updated=False
with target.open('xb') as f:s.save(f)
save('B0_probe_plan.json',dict(method=__doc__,original_input=str(src),modified_input=str(target),input_sha256=sha(src),historical_descriptor=str(BASE/'C1_input_descriptor.bin'),historical_descriptor_sha256=sha(BASE/'C1_input_descriptor.bin'),mask_sha256=sha(OUT/'A0_inherited_mask_roi.npy'),changed_pixels=int(np.any(aux!=rgb,axis=-1).sum()),changed_visible_input_pixels=int(np.any(aux[known]!=rgb[known],axis=-1).sum()),auxiliary='Nearest visible-support continuation, only where inherited output mask is exactly zero. Not physical terrain and never emitted as source pixels.',declared_check='Historical CR replay must reproduce archived C1. Auxiliary test must retain all visible input pixels exactly; measure resulting visible output change, face and limb separately. No automatic promotion.',limits=['Inherited presentation mask is not pure physical occultation; this probes filter coupling to invisible pixels only','Nearest continuation is a diagnostic perturbation, not an accepted repair','The newest user CR is baked into RGB; exact newest parameters not recovered or guessed']))
print('AUXILIARY PREPARED',int(np.any(aux!=rgb,axis=-1).sum()),'pixels changed, zero visible input changes',flush=True)
