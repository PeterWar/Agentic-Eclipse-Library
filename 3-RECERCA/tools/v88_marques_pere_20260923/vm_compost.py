"""Compositor per a la diagnosi: el de la V88 (Normal, Multiplica, Superposa, Sobreexposició lineal, Diferència, Aclarir) més «Lluminositat»
(LUMINOSITY, mode no separable de Photoshop: SetLum(Cb, Lum(Cs)), Lum = 0,30 R + 0,59 G + 0,11 B, amb ClipColor). Les capes d'ajust no s'emulen:
el jutge és el compost natiu que Photoshop desa dins del PSB."""
import numpy as np
from v86_compost import capa_box
def _lum(C): return 0.3 * C[..., 0] + 0.59 * C[..., 1] + 0.11 * C[..., 2]
def _clip(C):
    l = _lum(C)[..., None]; n = C.min(-1, keepdims=True); x = C.max(-1, keepdims=True)
    C = np.where(n < 0, l + (C - l) * l / np.maximum(l - n, 1e-9), C)
    C = np.where(x > 1, l + (C - l) * (1 - l) / np.maximum(x - l, 1e-9), C)
    return C
def set_lum(C, l): return _clip(C + (l - _lum(C))[..., None])
def comp(layers, H, W):
    Cb = np.zeros((H, W, 3), np.float32); ab = np.zeros((H, W), np.float32)
    for mode, F, a in layers:
        if mode == 'NORMAL': B = F
        elif mode == 'MULTIPLY': B = Cb * F
        elif mode == 'OVERLAY': B = np.where(Cb < 0.5, 2 * Cb * F, 1 - 2 * (1 - Cb) * (1 - F))
        elif mode == 'LINEAR_DODGE': B = np.clip(Cb + F, 0, 1)
        elif mode == 'DIFFERENCE': B = np.abs(Cb - F)
        elif mode == 'LIGHTEN': B = np.maximum(Cb, F)
        elif mode == 'LUMINOSITY': B = set_lum(Cb, _lum(F))
        else: raise ValueError(mode)
        Cs = (1 - ab[..., None]) * F + ab[..., None] * B; ao = a + ab * (1 - a)
        num = a[..., None] * Cs + (1 - a[..., None]) * ab[..., None] * Cb
        Cb = np.where(ao[..., None] > 0, num / np.maximum(ao[..., None], 1e-9), 0).astype(np.float32); ab = ao.astype(np.float32)
    return Cb, ab
