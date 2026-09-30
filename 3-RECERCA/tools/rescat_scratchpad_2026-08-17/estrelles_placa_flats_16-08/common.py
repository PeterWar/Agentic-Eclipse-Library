import numpy as np, rawpy

def load_planes(path, use_full=False):
    """Retorna dict canal->pla de Bayer (float64), sense restar pedestal.
    Canals: 'R','G1','B','G2' segons raw_pattern."""
    with rawpy.imread(path) as r:
        img = (r.raw_image if use_full else r.raw_image_visible).astype(np.float64)
        pat = r.raw_pattern.copy()
        if use_full:
            # ajusta la fase del patró als marges
            tm, lm = r.sizes.top_margin, r.sizes.left_margin
            # patró de raw_image_visible = pat; per raw_image cal desplaçar
            pat = np.roll(np.roll(pat, tm % 2, axis=0), lm % 2, axis=1)
    h = img.shape[0] // 2 * 2
    w = img.shape[1] // 2 * 2
    img = img[:h, :w]
    names = {0: 'R', 1: 'G1', 2: 'B', 3: 'G2'}
    out = {}
    for dy in (0, 1):
        for dx in (0, 1):
            out[names[int(pat[dy, dx])]] = img[dy::2, dx::2]
    return out


def masked_pedestal_canon(path):
    """Pedestal per canal dels píxels òpticament negres (marge esquerre) del CR3."""
    with rawpy.imread(path) as r:
        full = r.raw_image.astype(np.float64)
        lm = r.sizes.left_margin
        pat = r.raw_pattern.copy()
        tm = r.sizes.top_margin
        pat = np.roll(np.roll(pat, tm % 2, axis=0), lm % 2, axis=1)
    reg = full[:, 8:lm - 12]
    names = {0: 'R', 1: 'G1', 2: 'B', 3: 'G2'}
    out = {}
    for dy in (0, 1):
        for dx in (0, 1):
            sub = reg[dy::2, dx::2]
            out[names[int(pat[dy, dx])]] = (float(np.median(sub)), float(sub.mean()), float(sub.std()), sub.size)
    return out
