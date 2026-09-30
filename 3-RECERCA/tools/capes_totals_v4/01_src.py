"""01 — Exporta els 12 revelats V4 (TIFF u16 Display P3, 6960x4640) a npy per canal,
amb hash de la TIFF font i del npy. És la interfície entre revelat_normalitzat i la cadena."""
import numpy as np
import tifffile
from v4_lib import *

rep = {}
for i in ORDER:
    p = REVELAT / 'out' / f'v4_{LAYER_PREFIX[i]}.tif'
    a = tifffile.imread(str(p))
    assert a.shape == (FH, FW, 3) and a.dtype == np.uint16, (a.shape, a.dtype)
    hs = []
    for k in range(3):
        ch = np.ascontiguousarray(a[..., k])
        np.save(V4W / 'npy' / f'id{i}_{k}.npy', ch)
        hs.append(sha256_u16(ch))
    rep[str(i)] = dict(prefix=LAYER_PREFIX[i], tif=str(p), tif_sha256=__import__('hashlib').sha256(p.read_bytes()).hexdigest(),
                       canal_sha256_u16=hs)
    print(i, LAYER_PREFIX[i], hs[0][:12], flush=True)
jdump(rep, V4W / 'QA' / 'src_hashes.json')
