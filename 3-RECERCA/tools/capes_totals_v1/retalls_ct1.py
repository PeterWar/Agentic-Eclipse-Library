"""Retalls comparatius benchmark | candidat (mateixa escala), + vista sencera reduïda."""
import os, sys, numpy as np, tifffile
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__))
OUTD = os.path.join(D, 'previs'); os.makedirs(OUTD, exist_ok=True)
cand = np.load(os.path.join(D, sys.argv[1]), mmap_mode='r'); tag = sys.argv[2] if len(sys.argv)>2 else 'cand'
bm = tifffile.imread(os.path.expanduser('~/Downloads/Benchmark20Agost.tif'))
def to8(a):  # ja és imatge revelada; només 16->8
    return (np.asarray(a, np.float32)/257.0).clip(0,255).astype(np.uint8)
ZONES = {
  'limbe_protuberancia': (2400, 3250, 900),   # y0, x0, mida
  'creixent_perles': (2300, 4100, 900),
  'lluna_earthshine': (2290, 3590, 900),
  'corona_mitjana_W': (2300, 1800, 1200),
  'banda_traspas_E': (2100, 4700, 1400),
  'canto_TL': (0, 0, 1200),
  'canto_BR': (4153, 6448, 1200),
  'vora_dreta_mig': (2200, 6748, 900),
}
for nomz, (y0, x0, s) in ZONES.items():
    y1, x1 = min(y0+s, 5353), min(x0+s, 7648)
    a = to8(bm[y0:y1, x0:x1]); b = to8(cand[y0:y1, x0:x1])
    sep = np.full((a.shape[0], 8, 3), 255, np.uint8)
    Image.fromarray(np.concatenate([a, sep, b], axis=1)).save(os.path.join(OUTD, f'{tag}_{nomz}.jpg'), quality=92)
im = Image.fromarray(to8(cand[::4, ::4])); im.save(os.path.join(OUTD, f'{tag}_sencera_x4.jpg'), quality=90)
im = Image.fromarray(to8(bm[::4, ::4])); im.save(os.path.join(OUTD, f'benchmark_sencera_x4.jpg'), quality=90)
print('retalls a', OUTD)
