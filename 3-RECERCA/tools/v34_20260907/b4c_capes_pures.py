"""B4c · Les deu vistes pures (P01–P09, C01) amb EL MATEIX CODI de v31_purs sobre la base V32.

Els mòduls de `research/tools/v31_purs` (radial_filters, local_filters, wow_filters,
nafe_filter, polar_filters, conditional_filters) s'importen tal qual; només es
redirigeixen, ABANS d'importar-los, les rutes del seu `common` (cau, sortides, rebuts)
i la funció `readbase` perquè llegeixin `base_G_v32` i escriguin sota aquest paquet.
Cap fitxer de v31_purs es modifica. Els dylib i la font NAFE publicada són còpies
byte a byte (purs/). FNRGF (només domini, fora del PSB) no es repeteix.
"""
import os, sys, json, shutil, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PURS = ROOT / 'research/tools/v31_purs'
MINE = HERE / 'purs'
for p in (MINE / 'receipts', MINE / 'cau'):
    p.mkdir(parents=True, exist_ok=True)
# el `common` que volem és el de v31_purs (no el de v29): sys.path net
sys.path = [str(PURS)] + [p for p in sys.path if 'research/tools' not in p]
os.environ['V29_FINAL_GRID'] = '1'
import common as vc
import numpy as np
vc.C = MINE / 'cau'; vc.OUT = ROOT / 'output/v34_20260907/lliurables/vistes'; vc.D = MINE
CAU34 = HERE / 'cau'
def readbase():
    return np.load(CAU34 / 'base_G_v34.npy', mmap_mode='r'), np.load(CAU34 / 'support_v34.npy')
vc.readbase = readbase
for fn in ('nafe_native.dylib', 'sparse_conv.dylib', 'sources/nafe_published.py'):
    assert (MINE / fn).read_bytes() == (PURS / fn).read_bytes(), fn
import radial_filters, local_filters, wow_filters, nafe_filter, polar_filters, conditional_filters
for mod in (radial_filters, local_filters, wow_filters, nafe_filter, polar_filters, conditional_filters):
    assert mod.C == vc.C and mod.readbase is readbase and mod.D == vc.D, mod.__name__

def log(s):
    print(time.strftime('%H:%M:%S'), s, flush=True)

def main():
    which = sys.argv[1:] or ['radial', 'local', 'wow']
    a, m = readbase(); assert a.shape == (vc.H, vc.W) and m.shape == a.shape
    if 'radial' in which:
        radial_filters.main(); log('P01/P02 fets')
    if 'local' in which:
        local_filters.main(); log('P03/C01 fets')
    if 'wow' in which:
        wow_filters.main(); log('P04/P05 fets')
    if 'nafe' in which:
        nafe_filter.main(); log('P06 fet')
    if 'polar' in which:
        a, m = readbase(); a = np.array(a)
        polar_filters.make_polar(a, m); del a
        polar_filters.main(); log('P07/P08 fets')
    if 'swap' in which:
        a, m = readbase(); conditional_filters.swap(np.array(a), m); log('P09 fet')
    log('B4c fet')

if __name__ == '__main__':
    main()
