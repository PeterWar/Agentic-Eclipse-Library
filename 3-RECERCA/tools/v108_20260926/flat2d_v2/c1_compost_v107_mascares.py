"""c1 (V108, flat2d_v2) · El compost AMB LES MÀSCARES DE LA V107 (modes, opacitats, alfes i màscares llegides del PSB; capes visibles 3, 54, 41, 42,
47, 49, 51, 45, 46, 55, 56 sota la 234; sense capes d'ajust) fet amb els ràsters d'un ESTAT (L{id}_G/RGB.npy, com r3_estat_v98).
Còpia de marrons/m21_compost_v107_mascares.py amb la sortida a la carpeta flat2d_v2. Les alfes efectives (alfa × màscara de la V107) es
llegeixen de la memòria cau del pilot si hi són (només lectura) o es fan a flat2d_v2/mascares_v107/. Mateix compost per a ABANS i DESPRÉS.
Si l'estat té una alfa pròpia diferent de la de la V107 (L{id}_alfa.npy), s'avisa: el compost faria servir la de la V107.
Ús: c1_compost_v107_mascares.py <estat> <sortida.npy>"""
import sys, json, hashlib
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[4]; W, H = 10551, 7506
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924')); from jutge_comu import comp
EST, SORT = Path(sys.argv[1]), Path(sys.argv[2])
CAU_PILOT = ARREL / '4-RESULTATS/v108_20260926/marrons/pilot/tmp_mascares_v107'; TMP = ARREL / '4-RESULTATS/v108_20260926/flat2d_v2/mascares_v107'
p = PSB(str(ARREL / '1-PHOTOSHOP/V107.psb')); vis = [l for l in p.layers if l['visible'] and l['id'] in (3, 54, 41, 42, 47, 49, 51, 45, 46, 55, 56)]
A = {}
for l in vis:
    lid = l['id']; f = CAU_PILOT / f'L{lid}_alfa_efectiva_u16.npy'
    if not f.exists():
        TMP.mkdir(parents=True, exist_ok=True); f = TMP / f'L{lid}_alfa_efectiva_u16.npy'
        if not f.exists():
            a = np.ones((H, W), np.float32)
            if -1 in l['chans']: a *= p.channel_box(lid, -1, (0, 0, W, H)).astype(np.float32) / 65535
            if -2 in l['chans'] and l['mask'] and not l['mask']['disabled']: a *= p.channel_box(lid, -2, (0, 0, W, H), fill=(65535 if l['mask']['background'] == 255 else 0)).astype(np.float32) / 65535
            np.save(f, np.round(a * 65535).astype(np.uint16)); del a
    A[lid] = np.load(f, mmap_mode='r')
avisos = []
for l in vis:   # l'alfa de dada de l'estat ha de ser la de la V107 (si no, el compost no seria el del PSB muntat)
    fa = EST / f"L{l['id']}_alfa.npy"
    if fa.exists() and -1 in l['chans']:
        q = lambda v: np.round(np.round(v.astype(np.float64) * 32768 / 65535) * 65535 / 32768).astype(np.uint16)
        est = q(np.asarray(np.load(fa, mmap_mode='r'))); psb = p.channel_box(l['id'], -1, (0, 0, W, H))
        n = int((est != psb).sum())
        if n: avisos.append(dict(capa=l['id'], px_alfa_diferent_de_la_V107=n))
out = np.lib.format.open_memmap(SORT, mode='w+', dtype=np.float32, shape=(H, W))
R = {l['id']: np.load(EST / (f"L{l['id']}_G.npy" if l['id'] != 3 else 'L3_RGB.npy'), mmap_mode='r') for l in vis}
for y0 in range(0, H, 500):
    y1 = min(H, y0 + 500); capes = []
    for l in vis:
        F = np.asarray(R[l['id']][y0:y1], np.float32) / 65535; a = np.asarray(A[l['id']][y0:y1], np.float32) / 65535 * l['opacity'] / 255
        capes.append((l['blend'], F, a))
    C, _ = comp(capes, y1 - y0, W); out[y0:y1] = C.mean(-1)
out.flush()
Path(str(SORT).replace('.npy', '_REBUT.json')).write_text(json.dumps(dict(estat=str(EST), capes=[l['id'] for l in vis], avisos_alfa=avisos), ensure_ascii=False, indent=1))
print('FET', SORT, 'avisos alfa:', avisos, flush=True)
