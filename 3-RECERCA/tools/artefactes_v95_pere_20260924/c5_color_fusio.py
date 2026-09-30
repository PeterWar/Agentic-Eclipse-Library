"""c5 · El color de la fusió (fusion_starless, la que fan servir els ACHF isòtrops canal per canal) al voltant de la Lluna: ln(R/G) i ln(B/G) en pas de banda
12–60 px, i ln G igual, a 1:2, amb les marques de Pere de l'ACHF 01 (octàgon). Només lectura."""
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/artefactes_v95_pere_20260924'
FONTS = ARREL / '4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources'
cx, cy, R = 5375.787, 3775.977, 452.979; B = 900; y0, x0 = int(cy) - B, int(cx) - B; sl = (slice(y0, y0 + 2 * B), slice(x0, x0 + 2 * B))
Fu = np.asarray(np.load(FONTS / 'fusion_starless.npy', mmap_mode='r')[sl], np.float32); ok = np.all(np.isfinite(Fu), -1) & np.all(Fu > 0, -1)
Z = np.load(SORT / 'marques.npz'); mk = np.zeros((7506, 10551), bool); ox, oy = Z['283_origen']; g = Z['283_to_50_60']; mk[oy:oy + g.shape[0], ox:ox + g.shape[1]] = g; mk = mk[sl]
bp = lambda X: np.where(ok, cv2.GaussianBlur(X, (0, 0), 12) - cv2.GaussianBlur(X, (0, 0), 60), 0)
L = np.log(np.where(ok[..., None], Fu, 1)); rg = L[..., 0] - L[..., 1]; bg = L[..., 2] - L[..., 1]; lg = L[..., 1]
pan = []
for nom, X, rang in (('ln(R/G) · banda 12–60 px (±1 %)', bp(rg), 0.01), ('ln(B/G) · banda 12–60 px (±1 %)', bp(bg), 0.01), ('ln G · banda 12–60 px (±3 %)', bp(lg), 0.03), ('ln(B/G) sencer (±5 % entorn de la mediana)', np.where(ok, bg - np.median(bg[ok]), 0), 0.05)):
    im = np.stack([np.uint8(np.clip(0.5 + X / (2 * rang), 0, 1) * 255)] * 3, -1)
    cs, _ = cv2.findContours(mk.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(im, cs, -1, (255, 190, 0), 3); pan.append((nom, cv2.resize(im, (900, 900), interpolation=cv2.INTER_AREA)))
out = Image.new('RGB', (2 * 908, 2 * 934), 'white'); dr = ImageDraw.Draw(out); F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 18)
for i, (nom, im) in enumerate(pan): X0, Y0 = (i % 2) * 908, (i // 2) * 934; out.paste(Image.fromarray(im), (X0, Y0 + 32)); dr.text((X0 + 6, Y0 + 8), 'fusion_starless · ' + nom + ' · marques ACHF 01 (groc) · 1:2', fill='black', font=F)
out.save(SORT / 'COLOR_FUSIO_OCTAGON.png'); print('fet')
