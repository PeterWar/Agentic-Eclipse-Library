"""Compositor mínim per a la V88: el de la V86 (Normal, Multiplica, Superposa, Sobreexposició lineal, Diferència) més «Aclarir» (LIGHTEN,
el màxim per canal), que la V87 de Pere fa servir a la capa 76. Només per a comprovacions i vistes; les capes d'ajust no s'emulen."""
import numpy as np
from v86_compost import capa_box
def comp(layers, H, W):
    Cb = np.zeros((H, W, 3), np.float32); ab = np.zeros((H, W), np.float32)
    for mode, F, a in layers:
        if mode == 'NORMAL': B = F
        elif mode == 'MULTIPLY': B = Cb * F
        elif mode == 'OVERLAY': B = np.where(Cb < 0.5, 2 * Cb * F, 1 - 2 * (1 - Cb) * (1 - F))
        elif mode == 'LINEAR_DODGE': B = np.clip(Cb + F, 0, 1)
        elif mode == 'DIFFERENCE': B = np.abs(Cb - F)
        elif mode == 'LIGHTEN': B = np.maximum(Cb, F)
        else: raise ValueError(mode)
        Cs = (1 - ab[..., None]) * F + ab[..., None] * B; ao = a + ab * (1 - a)
        num = a[..., None] * Cs + (1 - a[..., None]) * ab[..., None] * Cb
        Cb = np.where(ao[..., None] > 0, num / np.maximum(ao[..., None], 1e-9), 0).astype(np.float32); ab = ao.astype(np.float32)
    return Cb, ab
