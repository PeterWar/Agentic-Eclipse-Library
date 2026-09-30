"""c7 · La vora de 9 px a tots els filtres: ràster de cada filtre (V95 = Artefactes_V95 llevat de la 52 i la 54, pintades) a 6:1 a dues marques del limbe,
amb el cercle del limbe de presentació (d = 0, vermell), d = 9 px (cian), el límit de dada de la franja d'un instant DMIN(θ) (groc) i les marques de Pere (taronja).
Més el perfil radial mitjà de cada filtre a d −5…20 (nivell i textura). Només lectura."""
import sys, json
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/artefactes_v95_pere_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
cx, cy, R = 5375.787, 3775.977, 452.979; Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); DMIN = Q['DMIN']; NB = len(DMIN)
p = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb')); Z = np.load(SORT / 'marques.npz')
FIL = [(41, 'P01 NRGF', '277'), (42, 'P01b NRGF estès', '276'), (51, '04 ACHF micro', '273'), (47, '03 ACHF r0', '275'), (43, 'P02 RHEF', '280'), (45, 'P02c RHEF 60°', '272'), (54, 'P03 MGN', '54'), (56, 'P05 WOW V95', '270')]
LLOCS = [(250, 4), (90, 4)]; w, zf = 50, 6; B = 520; y0b, x0b = int(cy) - B, int(cx) - B
yy, xx = np.mgrid[y0b:y0b + 2 * B, x0b:x0b + 2 * B]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
dmin = DMIN[(th / 360 * NB).astype(int) % NB]
def marca(clau):
    out = np.zeros((2 * B, 2 * B), bool)
    if f'{clau}_origen' not in Z.files: return out
    ox, oy = Z[f'{clau}_origen']
    for k in Z.files:
        if k.startswith(clau + '_') and not k.endswith('origen'):
            mm = Z[k]; big = np.zeros((7506, 10551), bool); big[oy:oy + mm.shape[0], ox:ox + mm.shape[1]] = mm; out |= big[y0b:y0b + 2 * B, x0b:x0b + 2 * B]
    return out
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); files = []; perf = {}
for lid, nom, clau in FIL:
    X = p.channel(lid, 0)[0][y0b:y0b + 2 * B, x0b:x0b + 2 * B].astype(np.float32) / 65535; A = p.channel(lid, -1)[0][y0b:y0b + 2 * B, x0b:x0b + 2 * B].astype(np.float32) / 65535; mk = marca(clau)
    perf[lid] = [round(float(X[(np.abs(d - dd) < 0.5) & (A > 0.5)].mean()), 3) if ((np.abs(d - dd) < 0.5) & (A > 0.5)).any() else None for dd in (-4, -2, 0, 1, 2, 3, 4, 6, 8, 10, 14, 20)]
    row = []
    for az, dd in LLOCS:
        px = int(cx + (R + dd) * np.cos(np.radians(az))) - x0b; py = int(cy - (R + dd) * np.sin(np.radians(az))) - y0b; c = X[py - w // 2:py + w // 2, px - w // 2:px + w // 2]
        lo, hi = np.percentile(c, (2, 98)); im = np.stack([np.uint8(np.clip((c - lo) / max(hi - lo, 1e-6), 0, 1) * 255)] * 3, -1); im = cv2.resize(im, (w * zf, w * zf), interpolation=cv2.INTER_NEAREST)
        sub = lambda Mm: cv2.resize(Mm[py - w // 2:py + w // 2, px - w // 2:px + w // 2].astype(np.uint8), (w * zf, w * zf), interpolation=cv2.INTER_NEAREST)
        for Mm, col in ((d >= 0, (255, 0, 0)), (d >= 9, (0, 255, 255)), (d >= dmin, (255, 230, 0)), (mk, (255, 120, 0))):
            s = sub(Mm); v = cv2.dilate(s, np.ones((3, 3), np.uint8)) - cv2.erode(s, np.ones((3, 3), np.uint8)); im[v > 0] = col
        row.append(im)
    files.append((lid, nom, row))
Wt = w * zf; out = Image.new('RGB', (2 * (Wt + 8) + 10, len(files) * (Wt + 26) + 40), 'white'); dr = ImageDraw.Draw(out)
dr.text((6, 8), 'Vora del limbe a cada filtre, 6:1 · vermell: limbe de presentació (d=0) · cian: d=9 px · groc: on comença la dada (DMIN) · taronja: marques de Pere', fill='black', font=F)
for j, (lid, nom, row) in enumerate(files):
    for i, im in enumerate(row):
        X0, Y0 = i * (Wt + 8), 40 + j * (Wt + 26); out.paste(Image.fromarray(im), (X0, Y0 + 20)); dr.text((X0 + 4, Y0 + 2), f'{lid} {nom} · {LLOCS[i][0]}°', fill='black', font=F)
out.save(SORT / 'VORA_LIMBE_FILTRES_6a1.png'); print('d:', [-4, -2, 0, 1, 2, 3, 4, 6, 8, 10, 14, 20]); [print(lid, perf[lid]) for lid, _, _ in FIL]
