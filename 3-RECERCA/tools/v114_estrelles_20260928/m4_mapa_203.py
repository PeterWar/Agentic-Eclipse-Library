"""m4 · V114 (Claude, 28-09-2026, nit): regenera la capa 203 «Mapa de N estrelles · HIP i TYC» amb la MATEIXA recepta de la V65
(3-RECERCA/tools/v65_pere_estrelles_20260914/s24_star_package.py, bloc de l'anotació: cercles, etiquetes i llegenda, Arial, mateixos colors i
mateix algorisme de col·locació), per a una llista d'estrelles del S22 (--treu <ids>) i una llegenda (--llegenda <json amb títol i línies>).
Control: sense --treu i amb la llegenda de la V65 ha de reproduir la 203 de la V113 bit a bit (RGB = ann·257, màscara = alfa de l'anotació).
Sortida: npz (R, G, B, M) del llenç sencer per a m3_munta_v114.py --c203."""
import sys, json, argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
ap = argparse.ArgumentParser(); ap.add_argument('sortida'); ap.add_argument('--treu', nargs='*', default=[]); ap.add_argument('--llegenda'); ap.add_argument('--control', action='store_true')
A = ap.parse_args()
cat = json.loads((R / '4-RESULTATS/v65_pere_estrelles_20260914/S22_final_catalog.json').read_text()); H, W = 7506, 10551
TITOL, LINIES = 'V65 · Estrelles recuperades', ['60 fonts puntuals corroborades en RAW', '62 identificacions · 2 parelles no resoltes', 'Sony A/C + Vixen · PSF gaussiana 3,53 px', 'Groc: HIP · Verd: identificació TYC al catàleg', 'S01–S60: V65_estrelles.csv', 'La mida és fotogràfica; el flux lineal és al catàleg.']
if A.llegenda: d = json.loads(Path(A.llegenda).read_text()); TITOL, LINIES = d['titol'], d['linies']
im = Image.new('RGBA', (W, H)); draw = ImageDraw.Draw(im)
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 30); head = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 48)
small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 31); placed = []
for r in cat['stars']:
    if r['id'] in A.treu: continue
    x, y = r['x'], r['y']; col = (255, 221, 68, 255) if r['HIP'] else (104, 245, 155, 255)
    txt = r['id'] + (' · HIP ' + str(r['HIP']) if r['HIP'] else '') + (' · doble no resolta' if r['unresolved_blend'] else '')
    box = draw.textbbox((0, 0), txt, font=font); tw, th = box[2], box[3]; best = None
    for dx, dy in [(22, -36), (22, 14), (-tw - 22, -36), (-tw - 22, 14), (22, 46), (-tw - 22, -70)]:
        xx, yy = x + dx, y + dy; bb = [xx - 3, yy - 3, xx + tw + 3, yy + th + 3]
        over = sum(max(0, min(bb[2], b[2]) - max(bb[0], b[0])) * max(0, min(bb[3], b[3]) - max(bb[1], b[1])) for b in placed)
        bad = 1000000 if min(bb[:2]) < 0 or bb[2] > W or bb[3] > H else 0; score = over + bad
        if best is None or score < best[0]: best = (score, xx, yy, bb)
    _, xx, yy, bb = best; placed.append(bb)
    draw.ellipse((x - 14, y - 14, x + 14, y + 14), outline=(0, 0, 0, 200), width=6); draw.ellipse((x - 14, y - 14, x + 14, y + 14), outline=col, width=3)
    draw.text((xx, yy), txt, font=font, fill=col, stroke_width=2, stroke_fill=(0, 0, 0, 230))
draw.rounded_rectangle((180, 6630, 1940, 7245), radius=28, fill=(10, 17, 20, 225), outline=(180, 192, 188, 220), width=2)
draw.text((225, 6675), TITOL, font=head, fill=(238, 242, 239, 255))
for i, line in enumerate(LINIES): draw.text((225, 6760 + 63 * i), line, font=small, fill=(225, 231, 225, 255))
ann = np.asarray(im); rgb = ann[..., :3].astype('uint16') * 257; M = (ann[..., 3].astype('uint16') * 257)
if A.control:
    from comu_v108 import PSB
    p = PSB(str(R / '1-PHOTOSHOP/V113.psb'))
    for cid, arr in ((0, rgb[..., 0]), (1, rgb[..., 1]), (2, rgb[..., 2]), (-2, M)):
        act, org = p.channel(203, cid); print('canal', cid, 'orig', org, 'diferents', int((act != arr).sum()), 'màx', int(np.abs(act.astype(int) - arr.astype(int)).max()), flush=True)
np.savez_compressed(A.sortida, R=rgb[..., 0], G=rgb[..., 1], B=rgb[..., 2], M=M)
print('fet', A.sortida, 'estrelles', sum(1 for r in cat['stars'] if r['id'] not in A.treu))
