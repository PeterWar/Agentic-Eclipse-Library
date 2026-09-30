"""03 — P3 (perles/diamant de la 1/3200) i P4 (cromosfera/protuberàncies de la 1/500 + anell de
limbe R4→R4+4) com a PÍXELS de fenomen, RE-MESURATS sobre els revelats V4 (proposta §4.2: els
llindars d'histèresi es re-validen sobre el ràster nou; el clip és a la zona protegida).
Diferència amb V3c: els nuclis cremats del revelat normalitzat s'afegeixen al cos de P3/P4
(al revelat nou les perles i la cromosfera clippen a blanc; el nucli cremat ÉS el fenomen).
Surt P3.npy/P4.npy float32 (1 = alfa zero de les capes superiors)."""
import numpy as np
from scipy import ndimage as ndi
from v4_lib import *

ell = ell_all()
xx, yy = canvas_grid()
rep = {}
# ---------- P3 (ID3 = 12_1/3200) ----------
mx3, mn3 = layer_maxmin_canvas(3)
d3 = d_moon(ell['3'], xx, yy)
ann = (d3 >= 400) & (d3 <= 600)
seed = ann & (mn3 >= 0.99)
allowed = ann & (mn3 >= 0.10)
lab, n = ndi.label(allowed)
keep = [int(l) for l in np.unique(lab[seed]) if l > 0 and np.count_nonzero(seed & (lab == l)) >= 3]
conn = np.isin(lab, keep)
core3 = conn & (mn3 >= 0.20)
P3m, dist3 = feather_from_core(core3, 3.0, 4.0)
comp, nc = ndi.label(core3)
areas = sorted(ndi.sum(core3, comp, range(1, nc + 1)).astype(int).tolist(), reverse=True)
ys, xs = np.nonzero(core3)
rep['P3'] = dict(font='ID3 12_1/3200 min(RGB), revelat V4 (clip inclòs)', anell_px=[400, 600], seed_min=0.99, allowed_min=0.10, core_min=0.20,
                 nucli_px=int(core3.sum()), components=int(nc), arees=areas[:12],
                 bbox=[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if core3.any() else None,
                 dilatacio_px=3.0, ploma_px=4.0, P_eq1_px=int((P3m >= 1).sum()), P_gt0_px=int((P3m > 0).sum()),
                 dist_max_protegit_a_fenomen_px=float(dist3[P3m > 0].max()))
print('P3', rep['P3'], flush=True)
np.save(V4W / 'masks/P3.npy', P3m)
np.save(V4W / 'masks/core3.npy', core3)
del mx3, mn3, ann, seed, allowed, lab, conn, comp
# ---------- P4 (ID4 = 11_1/500) ----------
R4c = layer_channel_canvas(4, 0)
G4c = layer_channel_canvas(4, 1)
_, mn4 = layer_maxmin_canvas(4)
d4 = d_moon(ell['4'], xx, yy)
R4 = R_eq(ell['4'])
cx4, cy4 = ell['4']['cx'], ell['4']['cy']
az4 = np.degrees(np.arctan2(-(yy - cy4), xx - cx4)) % 360
refz = (d4 > R4 + 35) & (d4 <= R4 + 100) & ~((az4 > 130) & (az4 < 220)) & (G4c > 0.01) & (mn4 < 0.99)
kRG = float(np.median(R4c[refz] / G4c[refz]))
exR = R4c - np.float32(kRG) * G4c
zona64 = (d4 > R4) & (d4 <= R4 + 64)
noclip = mn4 < 0.99
seed = zona64 & noclip & (exR >= 0.060)
allowed = zona64 & noclip & (exR >= 0.020)
lab, n = ndi.label(allowed)
keep = [int(l) for l in np.unique(lab[seed]) if l > 0 and np.count_nonzero(seed & (lab == l)) >= 3]
prom = np.isin(lab, keep)
limb = (d4 > R4) & (d4 <= R4 + 4)
sat = zona64 & (mn4 >= 0.99)          # nuclis cremats del revelat nou: cromosfera/limbe cremat
core4 = prom | limb | sat
P4m, dist4 = feather_from_core(core4, 4.0, 6.0)
comp, nc = ndi.label(prom)
areas = ndi.sum(prom, comp, range(1, nc + 1)).astype(int) if nc else np.array([])
order = np.argsort(-areas) if nc else []
desc = []
for j in list(order)[:10]:
    ys2, xs2 = np.nonzero(comp == j + 1)
    desc.append([int(areas[j]), [int(xs2.min()), int(ys2.min()), int(xs2.max()) + 1, int(ys2.max()) + 1]])
rep['P4'] = dict(font='ID4 11_1/500: excés vermell R − k·G + nuclis cremats (revelat V4)', k_RG=round(kRG, 4),
                 zona_px=[0, 64], seed_excess=0.060, allowed_excess=0.020,
                 prominencies_px=int(prom.sum()), components=int(nc), components_desc=desc,
                 limbe_px=int(limb.sum()), limbe_anell=[0, 4], sat_px=int(sat.sum()),
                 nucli_px=int(core4.sum()), dilatacio_px=4.0, ploma_px=6.0,
                 P_eq1_px=int((P4m >= 1).sum()), P_gt0_px=int((P4m > 0).sum()),
                 dist_max_protegit_a_fenomen_px=float(dist4[P4m > 0].max()),
                 extensio_max_sobre_limbe_px=float((d4[prom] - R4).max()) if prom.any() else 0.0)
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
