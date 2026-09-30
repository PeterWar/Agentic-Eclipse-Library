"""Retain user source chroma exactly while replacing monochrome earthshine luminance.
A single equal integer change to R,G,B preserves the chromatic solar component
through the inherited Normal layer mask. No clipping, new mask or hand retouch.
"""
from validation_common import *
a=np.load(OUT/'G2_candidate_rgb.npy').astype(np.int32);old=np.load(PREV/'A0_live_layer21_rgb.npy').astype(np.int32);delta=np.rint(np.mean(a-old,axis=-1)).astype(np.int32);new=old+delta[...,None];assert new.min()>=0 and new.max()<=65535
assert np.max(np.ptp(new-old,axis=-1))==0
np.save(OUT/'G3_candidate_rgb.npy',new.astype(np.uint16));save('G3_neutral_chroma.json',dict(method=__doc__,old_chromatic_differences_exact=True,clipped_pixels=0,max_adjustment_to_G2_DN16=int(abs(new-a).max())))
