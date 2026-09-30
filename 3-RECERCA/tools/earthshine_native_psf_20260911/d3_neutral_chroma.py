"""Retain user source chroma exactly while replacing monochrome earthshine luminance.
A single equal integer change to R,G,B preserves the chromatic solar component
through the inherited Normal layer mask. No clipping, new mask or hand retouch.
"""
from full_delta_common import *
PREV=ROOT/'output/earthshine_validation_20260911'
a=np.load(OUT/'C2_candidate_rgb.npy').astype(np.int32);old=np.load(ROOT/'output/earthshine_reconstruction_20260911/A0_live_layer21_rgb.npy').astype(np.int32);delta=np.rint(np.mean(a-old,axis=-1)).astype(np.int32);new=old+delta[...,None];assert new.min()>=0 and new.max()<=65535
assert np.max(np.ptp(new-old,axis=-1))==0
np.save(OUT/'C3_candidate_rgb.npy',new.astype(np.uint16));save('C3_neutral_chroma.json',dict(method=__doc__,old_chromatic_differences_exact=True,clipped_pixels=0,max_adjustment_to_C2_DN16=int(abs(new-a).max())))
