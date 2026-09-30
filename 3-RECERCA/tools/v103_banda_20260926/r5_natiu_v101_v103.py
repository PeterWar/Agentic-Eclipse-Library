"""r5 (V99 banda) · Vistes natives del Photoshop (el compost amb les capes d'ajust de Pere) de la V101 i la V103 costat a costat, a 4:1 (veí més proper),
als llocs de la banda sense dada. Fonts: vistes/V98_lluna.tif i vistes/V99_lluna.tif (retall [4600, 3000, 6150, 4550] del llenç).
Ús: r5_natiu_v98_v99.py <V98_lluna.tif> <V99_lluna.tif> <carpeta sortida>"""
import sys
from pathlib import Path
import numpy as np, tifffile, cv2
A = tifffile.imread(sys.argv[1]); B = tifffile.imread(sys.argv[2]); O = Path(sys.argv[3]); O.mkdir(parents=True, exist_ok=True)
def u8(x): return (x.astype(np.float32) / (65535 if x.dtype == np.uint16 else 255) * 255 + 0.5).clip(0, 255).astype(np.uint8)
A = u8(A[..., :3]); B = u8(B[..., :3])
LLOCS = {'dalt': (646, 283, 906, 413), 'dalt_esquerra': (386, 386, 526, 526), 'esquerra': (253, 706, 393, 846), 'baix_esquerra': (386, 1026, 526, 1166), 'baix': (646, 1189, 906, 1319), 'dreta': (1159, 706, 1299, 846)}
for nom, (x0, y0, x1, y1) in LLOCS.items():
    a = cv2.resize(A[y0:y1, x0:x1], None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST); b = cv2.resize(B[y0:y1, x0:x1], None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
    sep = np.full((a.shape[0], 16, 3), 255, np.uint8); cv2.imwrite(str(O / f'NATIU_{nom}_V101_V103_4a1.png'), cv2.cvtColor(np.hstack([a, sep, b]), cv2.COLOR_RGB2BGR)); print(nom)
