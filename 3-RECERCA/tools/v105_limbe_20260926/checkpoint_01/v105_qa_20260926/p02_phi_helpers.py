"""P02 read-only numerical helpers; no I/O, no fitting, no image filling.

phi_crop is bit-exact to the frozen producer's full cv2.INTER_LINEAR upsample
for the declared lunar box (verified in factorial_frozen_corrections.json).
"""
import numpy as np
import cv2

def phi_crop(phi_coarse, box_y0y1x0x1, q=4):
    y0,y1,x0,x1=map(int,box_y0y1x0x1)
    if not (0<=y0<y1<=phi_coarse.shape[0]*q and 0<=x0<x1<=phi_coarse.shape[1]*q):
        raise ValueError('Helper accepts only interior boxes; frozen full-canvas border replication is not inferred.')
    ay0=max(0,y0//q-1);ax0=max(0,x0//q-1)
    ay1=min(phi_coarse.shape[0],(y1+q-1)//q+1);ax1=min(phi_coarse.shape[1],(x1+q-1)//q+1)
    small=np.asarray(phi_coarse[ay0:ay1,ax0:ax1],np.float32)
    large=cv2.resize(small,(small.shape[1]*q,small.shape[0]*q),interpolation=cv2.INTER_LINEAR)
    return large[y0-ay0*q:y1-ay0*q,x0-ax0*q:x1-ax0*q]

def numerator_remove_phi_keep_b(numerator, phi_rgb, camera_gains=None):
    """N_cached=(N_pre+b*W)*exp(-phi); output keeps original additive b.

    Returns float64. This is a mathematical inverse of the saved multiplier,
    within saved float32 precision, not recovery of rounding bits from RAW.
    Gains act in camera RGB before the declared color gains and matrix.
    W is intentionally unchanged; callers must retain their declared policy.
    """
    out=np.asarray(numerator,np.float64)*np.exp(np.asarray(phi_rgb,np.float32))
    if camera_gains is not None:out*=np.asarray(camera_gains,np.float64)
    return out

def eligible_weight(weight,dreal,lo=.6,hi=2.):
    """Geometric ramp only. Negative noisy numerator values remain observations.

    Do not reject N<0: doing so would reintroduce a positive-selection bias.
    dreal>lo is not proof that the PSF/cromosphere contribution is absent.
    """
    t=np.clip((np.asarray(dreal)-lo)/(hi-lo),0,1)
    return np.asarray(weight)*((t*t*(3-2*t))[...,None])
