"""03b — Màscares de saturació per capa (plateau del sensor) i re-derivació de P3/P4 per a la V4.

Per què: amb els revelats normalitzats, el criteri antic (p50/p95 del codificat) NO detecta el
plateau de saturació, que ara seu a nivell scale_i (baix per a les capes llargues). La V4 ho mesura
a la FONT: píxel saturat ⟺ raw ≥ blanc (13995 als apilats — el stacker hi posa el blanc quan tots
els membres clippen—; 65535 als DNG convertits de CR3). Coordenades de LLENÇ.

P3 (autoritat de la 1/3200; zero per a 4,5,7,8,…): nuclis ≥3 px de sat_11 (v07 ≥ 34: perles i
cromosfera brillant) dins l'anell lunar 400–600 px, ∪ nuclis de sat_12 (v07 ≥ 210: perles/diamant,
clippen a tot arreu). Ploma 3+4 px com sempre.
P4 (autoritat de la 1/500; zero per a 5,7,8,…): nuclis de sat_10 (v07 ≥ 8,5: cromosfera) ∪ excés
vermell (com a V3c) ∪ anell de limbe R4→R4+4. Ploma 4+6 px.
"""
import numpy as np
from scipy import ndimage as ndi
from v4_lib import *
import rawpy

REVELAT_OUT = REVELAT / 'out'
ell = ell_all()
xx, yy = canvas_grid()
rep = {}

def sat_frame_from_dng(prefix):
    """Màscara de saturació del frame (6960x4640) llegint el DNG font (el convertit, pels CR3)."""
    sys.path.insert(0, str(HERE.parent / 'revelat_normalitzat'))
    import render_lineal as RL
    path = RL.dng_font(prefix)
    with rawpy.imread(str(path)) as raw:
        s = raw.sizes
        x = raw.raw_image[..., :3]
        white = float(raw.white_level)
        if (s.crop_width, s.crop_height) == (FW, FH) and (s.crop_left_margin or s.crop_top_margin):
            x = x[s.crop_top_margin:s.crop_top_margin + s.crop_height,
                  s.crop_left_margin:s.crop_left_margin + s.crop_width, :]
    return x.max(axis=2) >= (white - 1)

def sat_canvas_from_prefix(i):
    sat = sat_frame_from_dng(LAYER_PREFIX[i])
    l, t, w, h = FRAMES[i]
    out = np.zeros((CH, CW), bool)
    out[t:t+h, l:l+w] = sat
    return out

# ---------- sat de TOTES les capes (validesa i cadena) ----------
sat11 = sat_canvas_from_prefix(4)    # 1/500  (plateau: v07 ≥ 34,1)
sat12 = sat_canvas_from_prefix(3)    # 1/3200 (plateau: v07 ≥ 210,6)
sat10 = sat_canvas_from_prefix(5)    # 1/125  (plateau: v07 ≥ 8,53)
for i in ORDER:
    s = sat_canvas_from_prefix(i) if i not in (3, 4, 5) else {3: sat12, 4: sat11, 5: sat10}[i]
    np.save(V4W / 'npy' / f'sat_{i}.npy', s)
    print(f'sat id{i} ({LAYER_PREFIX[i]}): {s.sum():,} px', flush=True)

# ---------- P3: allò que clippa a la 1/500 o a la 1/3200 → autoritat ID3 (la 1/3200) ----------
# CORRECCIÓ V4b (22-08): a la V4 primera, el clip de la 1/500 anava a P4 (autoritat 11), i el
# compost hi mostrava el blanc cremat de la 1/500 — la protuberància quedava sense estructura ni
# color. Amb els revelats normalitzats, el que clippa a la 1/500 només té dades a la 1/3200.
mx3, mn3 = layer_maxmin_canvas(3)
_, mn4 = layer_maxmin_canvas(4)
d3 = d_moon(ell['3'], xx, yy)
ann = (d3 >= 400) & (d3 <= 600)
cand = ann & ((mn3 >= 0.99) | (mn4 >= 0.99))
lab, n = ndi.label(cand)
mides = ndi.sum(cand, lab, range(1, n + 1)) if n else []
keep = {int(l) for l, a in zip(range(1, n + 1), mides) if a >= 3}
core3 = np.isin(lab, list(keep)) if keep else np.zeros_like(cand)
clip11 = ann & (mn4 >= 0.99)          # per excloure'l de P4
P3m, dist3 = feather_from_core(core3, 3.0, 4.0)
comp, nc = ndi.label(core3)
areas = sorted(ndi.sum(core3, comp, range(1, nc + 1)).astype(int).tolist(), reverse=True) if nc else []
ys, xs = np.nonzero(core3)
rep['P3'] = dict(font='clip blanc de la 12_1/3200 ∪ clip de la 11_1/500 (V4b), anell lunar 400–600 px, components ≥3 px',
                 nucli_px=int(core3.sum()), components=int(nc), arees=areas[:12],
                 clip11_dins_P3_px=int((clip11 & core3).sum()),
                 bbox=[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if core3.any() else None,
                 dilatacio_px=3.0, ploma_px=4.0, P_eq1_px=int((P3m >= 1).sum()), P_gt0_px=int((P3m > 0).sum()),
                 dist_max_protegit_a_fenomen_px=float(dist3[P3m > 0].max()) if (P3m > 0).any() else 0.0)
print('P3', rep['P3'], flush=True)
np.save(V4W / 'masks/P3.npy', P3m)
np.save(V4W / 'masks/core3.npy', core3)
del mx3, mn3, cand, lab, comp

# ---------- P4: excés vermell + anell de limbe (autoritat 1/500), SENSE el seu clip ----------
R4c = layer_channel_canvas(4, 0)
G4c = layer_channel_canvas(4, 1)
d4 = d_moon(ell['4'], xx, yy)
R4 = R_eq(ell['4'])
cx4, cy4 = ell['4']['cx'], ell['4']['cy']
az4 = np.degrees(np.arctan2(-(yy - cy4), xx - cx4)) % 360
refz = (d4 > R4 + 35) & (d4 <= R4 + 100) & ~((az4 > 130) & (az4 < 220)) & (G4c > 0.01) & (mn4 < 0.99)
kRG = float(np.median(R4c[refz] / G4c[refz]))
exR = R4c - np.float32(kRG) * G4c
zona64 = (d4 > R4) & (d4 <= R4 + 64)
seed = zona64 & (mn4 < 0.99) & (exR >= 0.060)
allowed = zona64 & (mn4 < 0.99) & (exR >= 0.020)
lab, n = ndi.label(allowed)
keep = [int(l) for l in np.unique(lab[seed]) if l > 0 and np.count_nonzero(seed & (lab == l)) >= 3]
prom = np.isin(lab, keep) if keep else np.zeros_like(allowed)
limb = (d4 > R4) & (d4 <= R4 + 4)
core4 = (prom | limb) & ~clip11          # el clip de la 1/500 és de la 1/3200 (P3), mai blanc a la V4b
P4m, dist4 = feather_from_core(core4, 4.0, 6.0)
rep['P4'] = dict(font='excés vermell ∪ limbe R→R+4, sense el clip de la 1/500 (V4b: va a P3)', k_RG=round(kRG, 4),
                 prominencies_px=int(prom.sum()), limbe_px=int(limb.sum()), nucli_px=int(core4.sum()),
                 dilatacio_px=4.0, ploma_px=6.0, P_eq1_px=int((P4m >= 1).sum()), P_gt0_px=int((P4m > 0).sum()),
                 dist_max_protegit_a_fenomen_px=float(dist4[P4m > 0].max()) if (P4m > 0).any() else 0.0)
print('P4', rep['P4'], flush=True)
np.save(V4W / 'masks/P4.npy', P4m)
np.save(V4W / 'masks/core4.npy', core4)
np.save(V4W / 'masks/prom4.npy', prom)
jdump(rep, V4W / 'QA/proteccio_P3_P4.json')

# PNG de QA
x0, y0 = 3578 - 512, 2653 - 512
I4 = np.repeat(stretch(G4c, 0, 0.3)[y0:y0 + 1024, x0:x0 + 1024][..., None], 3, 2)
ov = I4.copy()
ov[..., 0] = np.maximum(ov[..., 0], core4[y0:y0 + 1024, x0:x0 + 1024])
ov[..., 1] = np.maximum(ov[..., 1], core3[y0:y0 + 1024, x0:x0 + 1024])
save_png(np.concatenate([I4, ov, np.repeat(P4m[y0:y0 + 1024, x0:x0 + 1024][..., None], 3, 2)], 1),
         V4W / 'QA/proteccio_P3_P4_protuberancia.png')
x0, y0 = 3607 - 512, 2585 - 512
I3 = np.repeat(stretch(layer_channel_canvas(3, 1), 0, 0.5)[y0:y0 + 1024, x0:x0 + 1024][..., None], 3, 2)
ov = I3.copy()
ov[..., 1] = np.maximum(ov[..., 1], core3[y0:y0 + 1024, x0:x0 + 1024])
ov[..., 0] = np.maximum(ov[..., 0], core4[y0:y0 + 1024, x0:x0 + 1024] * 0.5)
save_png(np.concatenate([I3, ov, np.repeat(P3m[y0:y0 + 1024, x0:x0 + 1024][..., None], 3, 2)], 1),
         V4W / 'QA/proteccio_P3_perles.png')
print('PNG QA escrits', flush=True)
