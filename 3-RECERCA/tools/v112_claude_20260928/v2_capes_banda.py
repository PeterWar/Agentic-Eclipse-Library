"""V112 (Claude): vista de banda (18–240 px, blocs 6×6) del canal G de cada capa (base i filtres) d'un PSB, per saber a quin pis
neix un artefacte. Desa un .npy per capa (log G − gaussiana σ40 blocs, suavitzat σ3 blocs) a SORTIDA_DIR. Ús: v2_capes_banda.py PSB SORTIDA_DIR [ids…]"""
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
p = PSB(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
ids = [int(v) for v in sys.argv[3:]] or [3, 54, 41, 42, 47, 49, 51, 45, 46, 55, 56]
B = 6; H, W = p.height, p.width; h, w = H // B, W // B
for lid in ids:
    L = p.layer(lid)
    g = p.channel_box(lid, 1, (0, 0, W, H)).astype(np.float64)
    a = p.channel_box(lid, -1, (0, 0, W, H))
    val_full = (a > 0) if a is not None else np.ones((H, W), bool)
    gb = g[:h*B, :w*B].reshape(h, B, w, B).mean((1, 3)); vb = val_full[:h*B, :w*B].reshape(h, B, w, B).all((1, 3)) & (gb > 30)
    lg = np.where(vb, np.log(np.maximum(gb, 1)), 0)
    num = ndi.gaussian_filter(lg, 40); den = ndi.gaussian_filter(vb.astype(float), 40)
    hp = np.where(vb, lg - num / np.maximum(den, 1e-3), 0)
    n2 = ndi.gaussian_filter(hp, 3); d2 = ndi.gaussian_filter(vb.astype(float), 3)
    hp = np.where(vb, n2 / np.maximum(d2, 1e-3), np.nan).astype(np.float32)
    np.save(out / f'L{lid}.npy', hp)
    print(lid, L['name'], L['blend'], L['opacity'], 'mask' if L['mask'] else '', 'p99|hp|', float(np.nanpercentile(np.abs(hp), 99)))
