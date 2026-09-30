"""c2 · Les marques de Pere de Artefactes_V95.psb sobre el ràster del filtre (a 1/4), amb les vores candidates superposades:
mapa de resolució σ (fixed_inputs/resolution_sigma.npy, nivells), suport Vixen i Sony (sources_v29), pes Vixen 0,5 (weight_vixen_v42), caixa de la franja A3A,
caixa S4, isofotes de ln base_G. Una làmina per filtre. Només lectura; vistes a 4-RESULTATS/artefactes_v95_pere_20260924/."""
import sys, json
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/artefactes_v95_pere_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
V85D = ARREL / '4-RESULTATS/v85_regeneracio_20260922'; FONTS = V85D / 'd4_baseline/products/sources'
W, H = 10551, 7506; f = 4; w, h = W // f, H // f
red = lambda X, it=cv2.INTER_AREA: cv2.resize(np.asarray(X, np.float32), (w, h), interpolation=it)
sig = red(np.load(V85D / 'fixed_inputs/resolution_sigma.npy', mmap_mode='r')); vs = red(np.load(V85D / 'sources_v29/vixen_support.npy', mmap_mode='r').astype(np.float32)) > 0.5
ss = red(np.load(V85D / 'sources_v29/sony_support.npy', mmap_mode='r').astype(np.float32)) > 0.5; wv = red(np.load(V85D / 'b3_baseline/cau/weight_vixen_v42.npy', mmap_mode='r'))
lg = red(np.log(np.maximum(np.load(FONTS / 'base_G.npy', mmap_mode='r'), 1e-6)))
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]
s4 = np.load(V85D / 's4_baseline/cau/s4_recomposicio_box.npz'); s4b = [int(v) for v in s4['box']] if 'box' in s4.files else None
print('σ: mín', round(float(sig.min()), 2), 'màx', round(float(sig.max()), 2), 'nivells únics (arrodonits 0,1)', len(np.unique(np.round(sig, 1))), '| caixa S4', s4b, '| claus s4', s4.files)
Z = np.load(SORT / 'marques.npz'); M = json.loads((SORT / 'MARQUES.json').read_text())['marques']
p = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb'))
def contorn(img, mask, col, gruix=1):
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE); cv2.drawContours(img, cs, -1, col, gruix)
def marca_full(clau):
    grups = [k for k in Z.files if k.startswith(clau + '_') and not k.endswith('origen')]; out = np.zeros((H, W), bool); x0, y0 = Z[f'{clau}_origen']
    for g in grups: mm = Z[g]; out[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]] |= mm
    return out
FIL = {'283': 50, '282': 53, '273': 51, '52': 52, '280': 43, '270': 56}
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 22)
for clau, lid in FIL.items():
    if clau not in M and clau + '_pintat' not in M: continue
    X = p.channel(lid, 0)[0].astype(np.float32) / 65535; lo, hi = np.percentile(X[::8, ::8], (1, 99)); img = np.stack([np.uint8(np.clip((red(X) - lo) / (hi - lo), 0, 1) * 200)] * 3, -1)
    for nivell, col in ((1.0, (0, 200, 255)), (2.0, (0, 120, 255)), (4.0, (80, 0, 255)), (8.0, (180, 0, 200))): contorn(img, sig >= nivell, col)
    contorn(img, vs, (0, 255, 0), 2); contorn(img, ss, (255, 0, 0), 2); contorn(img, wv > 0.5, (255, 255, 0), 1)
    for lv, col in zip(np.percentile(lg[vs | ss], (99, 97, 94, 90)), ((255, 150, 150), (255, 110, 110), (255, 70, 70), (230, 40, 40))): contorn(img, lg >= lv, col)
    cv2.rectangle(img, (qx0 // f, qy0 // f), (qx1 // f, qy1 // f), (255, 255, 255), 1)
    if s4b: cv2.rectangle(img, (s4b[2] // f, s4b[0] // f), (s4b[3] // f, s4b[1] // f), (200, 200, 200), 1)
    mk = red(marca_full(clau if clau in M else clau).astype(np.float32)) > 0.1 if clau in M else red(marca_full(clau).astype(np.float32)) > 0.1
    ov = img.copy(); ov[mk] = (255, 210, 0); img = cv2.addWeighted(ov, 0.45, img, 0.55, 0)
    im = Image.fromarray(img); dr = ImageDraw.Draw(im)
    dr.text((10, 10), f'Capa {lid} amb les marques de Pere (groc translúcid). Contorns: σ resolució ≥1/2/4/8 (cian→lila), suport Vixen (verd), suport Sony (vermell),', fill='white', font=F)
    dr.text((10, 38), 'pes Vixen 0,5 (groc), isofotes ln base_G (rosa→vermell), caixa franja A3A (blanc), caixa S4 (gris). 1/4.', fill='white', font=F)
    im.save(SORT / f'SUPERPOSICIO_capa_{lid}.png'); print('fet', lid)
