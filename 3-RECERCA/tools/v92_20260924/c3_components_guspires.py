"""c3 (V92) · Les taques de la capa de guspires que Pere marca en gris: són components aïllats al llindar de 2·soroll (MAD) del top-hat de la 76?
Detecció amb HISTÈRESI (com a l'extracció de fonts): es queden només els components del top-hat > 2·σ que tenen algun píxel > kσ (llavor).
Mesura, per a k = 3, 4, 5, quants components i píxels queden, i quants toquen les marques grises. Sortida: C3_COMPONENTS.json."""
from pathlib import Path
import json, sys
import numpy as np, cv2
from scipy import ndimage as ndi
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v92_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
BXp = (4740, 3470, 5020, 4040); x0, y0, x1, y1 = BXp; h, w = y1 - y0, x1 - x0
p = PSB(str(ARREL / '1-PHOTOSHOP/V91.psb'))
F = np.stack([p.channel_box(76, c, BXp) for c in range(3)], -1).astype(np.float32) / 65535; L = 0.3 * F[..., 0] + 0.59 * F[..., 1] + 0.11 * F[..., 2]
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
TH = cv2.morphologyEx(L, cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
refz = (((th >= 143) & (th <= 154)) | ((th >= 201) & (th <= 212))) & (d > 15) & (d < 60); sd = float(np.median(np.abs(TH[refz] - np.median(TH[refz])))) * 1.4826
Z = np.load(SORT / 'P1B_GUSPIRES.npz'); reg = Z['alfa'].astype(np.float32) / 65535
a1 = p.channel_box(264, -1, BXp).astype(np.float32) / 65535; r1 = np.stack([p.channel_box(264, c, BXp) for c in range(3)], -1).astype(np.float32) / 257
gris = (a1 > 0.03) & (np.abs(r1[..., 0] - r1[..., 1]) < 14) & (np.abs(r1[..., 1] - r1[..., 2]) < 14); gris_d = cv2.dilate(gris.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
feble = (TH > 2 * sd) & (reg > 0.02); lab, n = ndi.label(feble, structure=np.ones((3, 3))); pic = ndi.maximum(TH, lab, index=np.arange(1, n + 1)) / sd; mida = ndi.sum(np.ones_like(TH), lab, index=np.arange(1, n + 1))
toca = np.array([bool(gris_d[lab == k].any()) for k in range(1, n + 1)])
rep = dict(soroll_sigma=round(sd, 6), components_2sigma=int(n), px_2sigma=int(feble.sum()), marques_grises_px=int(gris.sum()),
           components_que_toquen_marques=[dict(pic_sigma=round(float(pic[k]), 2), mida_px=int(mida[k])) for k in np.flatnonzero(toca)],
           resta_components_pic_sigma_percentils={q: round(float(np.percentile(pic[~toca], q)), 2) for q in (10, 25, 50, 75, 90)} if (~toca).any() else None, llavor={})
for k in (3, 4, 5, 6):
    keep = pic >= k; rep['llavor'][f'{k}sigma'] = dict(components=int(keep.sum()), px=int(mida[keep].sum()), fraccio_px=round(float(mida[keep].sum() / max(mida.sum(), 1)), 3),
                                                      marques_eliminades=int((toca & ~keep).sum()), marques_que_queden=int((toca & keep).sum()))
(SORT / 'C3_COMPONENTS.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); print(json.dumps(rep, ensure_ascii=False))
