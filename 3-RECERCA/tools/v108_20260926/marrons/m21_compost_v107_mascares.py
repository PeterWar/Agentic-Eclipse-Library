"""m21 · El compost AMB LES TEVES MÀSCARES de la V107 (modes, opacitats, alfes i màscares llegides del PSB; capes visibles 3, 54, 41, 42, 47,
49, 51, 45, 46, 55, 56 sota la 234; sense capes d'ajust) fet amb els ràsters d'un ESTAT (carpeta L{id}_G/RGB.npy, com r3_estat_v98).
Serveix per comparar ABANS (estat de la variant E, el de la V104–V107) i DESPRÉS (estat del pilot amb el flat 2D) amb exactament les
mateixes màscares. Es fa per franges de 500 files. Sortida: <sortida>.npy (mitjana RGB 0–1, float32, llenç sencer).
Ús: m21_compost_v107_mascares.py <estat> <sortida.npy>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924')); from jutge_comu import comp
EST, SORT = Path(sys.argv[1]), Path(sys.argv[2]); TMP = OUT / 'pilot/tmp_mascares_v107'; TMP.mkdir(parents=True, exist_ok=True)
p = PSB(str(ARREL / '1-PHOTOSHOP/V107.psb')); vis = [l for l in p.layers if l['visible'] and l['id'] in (3, 54, 41, 42, 47, 49, 51, 45, 46, 55, 56)]
A = {}
for l in vis:
    lid = l['id']; f = TMP / f'L{lid}_alfa_efectiva_u16.npy'
    if not f.exists():
        a = np.ones((H, W), np.float32)
        if -1 in l['chans']: a *= p.channel_box(lid, -1, (0, 0, W, H)).astype(np.float32) / 65535
        if -2 in l['chans'] and l['mask'] and not l['mask']['disabled']: a *= p.channel_box(lid, -2, (0, 0, W, H), fill=(65535 if l['mask']['background'] == 255 else 0)).astype(np.float32) / 65535
        np.save(f, np.round(a * 65535).astype(np.uint16)); del a
    A[lid] = np.load(f, mmap_mode='r')
out = np.lib.format.open_memmap(SORT, mode='w+', dtype=np.float32, shape=(H, W))
R = {l['id']: np.load(EST / (f"L{l['id']}_G.npy" if l['id'] != 3 else 'L3_RGB.npy'), mmap_mode='r') for l in vis}
for y0 in range(0, H, 500):
    y1 = min(H, y0 + 500); capes = []
    for l in vis:
        F = np.asarray(R[l['id']][y0:y1], np.float32) / 65535; a = np.asarray(A[l['id']][y0:y1], np.float32) / 65535 * l['opacity'] / 255
        capes.append((l['blend'], F, a))
    C, _ = comp(capes, y1 - y0, W); out[y0:y1] = C.mean(-1); print('franja', y0, flush=True) if y0 % 2000 == 0 else None
out.flush(); print('FET', SORT)
