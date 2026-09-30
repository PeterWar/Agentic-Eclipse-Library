"""Retalls a tres bandes per al panell: benchmark | D_trim | B_trim, amb etiquetes."""
import os, numpy as np, tifffile
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.abspath(__file__))
OUTD = os.path.join(D, 'panel'); os.makedirs(OUTD, exist_ok=True)
bm = tifffile.imread(os.path.expanduser('~/Downloads/Benchmark20Agost.tif'))
cd = np.load(os.path.join(D, 'compost_D_pont_135_195_trim.npy'), mmap_mode='r')
cb = np.load(os.path.join(D, 'compost_B_pont_15_28_trim.npy'), mmap_mode='r')
def to8(a): return (np.asarray(a, np.float32)/257.0).clip(0,255).astype(np.uint8)
ZONES = {
  'limbe_protuberancia': (2400, 3250, 900),
  'creixent_perles_E': (2300, 4100, 900),
  'lluna_sencera': (2270, 3560, 960),
  'limbe_inferior_bombolles': (3050, 3700, 700),
  'banda_traspas_NE': (1500, 4600, 1400),
  'corona_mitjana_S': (3300, 3400, 1400),
  'camp_llunya_TL': (100, 300, 1400),
}
for nomz, (y0, x0, s) in ZONES.items():
    y1, x1 = min(y0+s, 5353), min(x0+s, 7648)
    tiles = [to8(bm[y0:y1, x0:x1]), to8(cd[y0:y1, x0:x1]), to8(cb[y0:y1, x0:x1])]
    lab = ['BENCHMARK (SF10)', 'CANDIDAT D', 'CANDIDAT B']
    sep = np.full((tiles[0].shape[0], 8, 3), 255, np.uint8)
    out = tiles[0]
    for t in tiles[1:]:
        out = np.concatenate([out, sep, t], axis=1)
    im = Image.fromarray(out); dr = ImageDraw.Draw(im)
    for k in range(3):
        dr.rectangle([k*(s+8)+6, 6, k*(s+8)+250, 34], fill=(0,0,0))
        dr.text((k*(s+8)+12, 12), lab[k], fill=(255,255,0))
    im.save(os.path.join(OUTD, f'3B_{nomz}.jpg'), quality=92)
# vistes senceres x4
for nom, img in (('benchmark', bm), ('candidatD', cd), ('candidatB', cb)):
    Image.fromarray(to8(img[::4, ::4])).save(os.path.join(OUTD, f'sencera_{nom}_x4.jpg'), quality=90)
print('panel a', OUTD)
