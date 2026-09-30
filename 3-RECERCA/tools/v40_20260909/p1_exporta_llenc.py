"""P1 (V40) · LLENÇ SENCER per a Pere («amb retalls no ho veig bé»): per a cada capa demanada, la V38 i la candidata (les u16 vives de la cadena) en
TIFF de 16 bits a resolució plena (per obrir-les sobre el projecte al Photoshop) i en PNG a mida ½ (per alternar-les a l'ordinador o al mòbil).
Ús: p1_exporta_llenc.py <etiqueta> 01 P03 P05 …"""
from comu40 import *
import tifffile
from PIL import Image
LL = OUT40 / 'lliurables/llenc'; LL.mkdir(parents=True, exist_ok=True)
SRC = {'01': (CAU38 / '01_v38_u16.npy', CAU39 / '01_v39_u16.npy'), '04': (CAU38 / '04_v38_u16.npy', CAU39 / '04_v39_u16.npy'), '05': (CAU38 / '05_v38_u16.npy', CAU39 / '05_v39_u16.npy'), '06': (CAU38 / '06_v38_u16.npy', CAU39 / '06_v39_u16.npy'),
       'P03': (ROOT / 'research/tools/v38_20260908/purs/cau/P03_MGN_u16.npy', PC39 / 'P03_MGN_u16.npy'), 'P04': (ROOT / 'research/tools/v38_20260908/purs/cau/P04_WOW_u16.npy', PC39 / 'P04_WOW_u16.npy'), 'P05': (ROOT / 'research/tools/v38_20260908/purs/cau/P05_WOW_bilateral_u16.npy', PC39 / 'P05_WOW_bilateral_u16.npy')}


def main():
    tag = sys.argv[1]; capes = sys.argv[2:]
    for k in capes:
        for lab, p in (('V38', SRC[k][0]), (tag, SRC[k][1])):
            a = np.asarray(np.load(p, mmap_mode='r')); assert a.shape == (H, W) and a.dtype == np.uint16
            tifffile.imwrite(LL / f'{k}_{lab}_16bit.tif', a, photometric='minisblack', compression='zlib')
            half = (a.reshape(H // 2, 2, W // 2, 2).astype(np.float32).mean(axis=(1, 3)) / 257.0).astype(np.uint8) if H % 2 == 0 and W % 2 == 0 else (a[:H // 2 * 2, :W // 2 * 2].reshape(H // 2, 2, W // 2, 2).astype(np.float32).mean(axis=(1, 3)) / 257.0).astype(np.uint8)
            Image.fromarray(half).save(LL / f'{k}_{lab}_mig.png'); log(f'{k} {lab}: TIFF 16 bits sencer + PNG ½ ({sha(p)[:12]}…)')
    log('P1 fet')


if __name__ == '__main__':
    main()
