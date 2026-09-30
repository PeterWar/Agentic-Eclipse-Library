"""p0 (V109 · perles_psb) · Retalla el COMPOST FUSIONAT (Image Data, el que desa el Photoshop amb les capes d'ajust) de la V107 i la V108
a la caixa del limbe (tota la Lluna + 60 px) i el desa en uint16. Només lectura dels PSB.
Sortida: 4-RESULTATS/v109_perles_20260927/perles_psb/FUS_V107.npy, FUS_V108.npy (h, w, 3) i CAIXA.json"""
import struct, json, hashlib
from pathlib import Path
import numpy as np
R0 = Path(__file__).resolve().parents[4]; OUT = R0 / '4-RESULTATS/v109_perles_20260927/perles_psb'
CAIXA = (4840, 3240, 5912, 4312)
def fusionat(p, box):
    with open(p, 'rb') as f:
        hdr = f.read(26); nch = struct.unpack('>H', hdr[12:14])[0]; h, w = struct.unpack('>II', hdr[14:22])
        n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>Q', f.read(8))[0]; f.seek(n, 1)
        pos = f.tell(); assert struct.unpack('>H', f.read(2))[0] == 0
    mm = np.memmap(p, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, h, w)); x0, y0, x1, y1 = box
    return np.stack([np.asarray(mm[c, y0:y1, x0:x1]).astype(np.uint16) for c in range(3)], -1)
for v in ('V107', 'V108'):
    a = fusionat(R0 / f'1-PHOTOSHOP/{v}.psb', CAIXA); np.save(OUT / f'FUS_{v}.npy', a); print(v, a.shape, a.mean(axis=(0, 1)))
(OUT / 'CAIXA.json').write_text(json.dumps(dict(caixa_x0_y0_x1_y1=CAIXA), indent=1))
