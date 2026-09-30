"""Compositor mínim per a la V86 (Normal, Multiplica, Superposa, Sobreexposició lineal, Diferència) amb alfa de fons, com Photoshop
per a aquests modes. Només per a: la cantonada (capes de sota, sense capes d'ajust) i les comprovacions de cobertura i de vistes.
Les capes d'ajust de Pere (Luz, Niveles…) no s'emulen: les vistes finals les fa Photoshop."""
import numpy as np
def comp(layers, H, W):
    """layers: llista de (mode, rgb[H,W,3] 0–1, a[H,W] 0–1) de baix a dalt. Retorna (color, cobertura)."""
    Cb = np.zeros((H, W, 3), np.float32); ab = np.zeros((H, W), np.float32)
    for mode, F, a in layers:
        if mode == 'NORMAL': B = F
        elif mode == 'MULTIPLY': B = Cb * F
        elif mode == 'OVERLAY': B = np.where(Cb < 0.5, 2 * Cb * F, 1 - 2 * (1 - Cb) * (1 - F))
        elif mode == 'LINEAR_DODGE': B = np.clip(Cb + F, 0, 1)
        elif mode == 'DIFFERENCE': B = np.abs(Cb - F)
        else: raise ValueError(mode)
        Cs = (1 - ab[..., None]) * F + ab[..., None] * B; ao = a + ab * (1 - a)
        num = a[..., None] * Cs + (1 - a[..., None]) * ab[..., None] * Cb
        Cb = np.where(ao[..., None] > 0, num / np.maximum(ao[..., None], 1e-9), 0).astype(np.float32); ab = ao.astype(np.float32)
    return Cb, ab

def capa_box(p, lid, box, rgb=None, mask=None):
    """(mode, rgb, alfa efectiva) d'una capa d'un PSB (psb69) a box=(x0,y0,x1,y1); rgb/mask (uint16 llenç sencer) substitueixen els del fitxer."""
    L = p.layer(lid); x0, y0, x1, y1 = box; h, w = y1 - y0, x1 - x0
    if rgb is None: F = np.stack([p.channel_box(lid, c, box) for c in range(3)], -1).astype(np.float32) / 65535
    else: F = np.repeat((rgb[y0:y1, x0:x1].astype(np.float32) / 65535)[..., None], 3, -1) if rgb.ndim == 2 else rgb[y0:y1, x0:x1].astype(np.float32) / 65535
    a = p.channel_box(lid, -1, box).astype(np.float32) / 65535 if -1 in L['chans'] else np.ones((h, w), np.float32)
    if mask is not None: m = mask[y0:y1, x0:x1].astype(np.float32) / 65535
    elif L['mask'] is not None and -2 in L['chans']: m = p.channel_box(lid, -2, box, fill=65535 if L['mask']['background'] == 255 else 0).astype(np.float32) / 65535
    else: m = np.ones((h, w), np.float32)
    return (L['blend'], F, a * m * (L['opacity'] / 255.0))
