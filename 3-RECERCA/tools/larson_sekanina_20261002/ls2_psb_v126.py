"""LS2 · V126.psb = la V125-FINAL.psb de Pere (49 capes, intactes, i la mateixa imatge fusionada) + 2 capes Larson-Sekanina
OCULTES a sobre de tot (la «Capa 1» de Pere és opaca: el que vagi a sota no es veu), en Superposar al 20 %:
  «Larson-Sekanina 0,4° · V120 sense estrelles» i «Larson-Sekanina 1° · V120 sense estrelles».
Gris 0,5 = neutre; transparent on el filtre no existeix (sense dada, protuberàncies, franja del limbe).  La V125-FINAL no es toca.
Ús: python ls2_psb_v126.py <carpeta amb ls_*_v.npy i ls_*_alfa.npy>"""
import sys, os, json, time, hashlib
from pathlib import Path
import numpy as np
A = Path(__file__).resolve().parents[3]                # 4-Photoshop
sys.path.insert(0, str(A / 'Sortides/apod_anotada_20260930')); import psd16
from psd_tools import PSDImage
from psd_tools.constants import BlendMode
D = Path(sys.argv[1])
SRC = A / '1-PHOTOSHOP/V125-FINAL.psb'
DST = A / '1-PHOTOSHOP/V126.psb'
assert not DST.exists(), DST
t0 = time.time()
src_sha = hashlib.file_digest(open(SRC, 'rb'), 'sha256').hexdigest()
psd = PSDImage.open(SRC); n0 = len(list(psd)); noms0 = [l.name for l in psd]
assert (psd.width, psd.height, psd.depth) == (7933, 5021, 16)
noves = []
for d, nom in (("0.4", "Larson-Sekanina 0,4° · V120 sense estrelles"), ("1.0", "Larson-Sekanina 1° · V120 sense estrelles")):
    v = np.load(D / f'ls_{d}_v.npy'); al = np.load(D / f'ls_{d}_alfa.npy')
    arr = np.empty((5021, 7933, 4), np.uint16)
    g16 = np.round(np.clip(v, 0, 1) * 65535).astype(np.uint16)
    for c in range(3): arr[..., c] = g16
    arr[..., 3] = np.round(np.clip(al, 0, 1) * 65535).astype(np.uint16)
    lay = psd16.capa(psd, nom, arr)
    lay.blend_mode = BlendMode.OVERLAY; lay.opacity = round(0.20 * 255); lay.visible = False
    noves.append(nom)
    print(f'capa «{nom}» {time.time() - t0:.0f} s')
psd16.a_lr16(psd)
with open(DST, 'wb') as fh:          # la imatge fusionada i els recursos (ICC) es queden els de la V125-FINAL
    psd._record.write(fh)
dst_sha = hashlib.file_digest(open(DST, 'rb'), 'sha256').hexdigest()
# comprovació: es reobre; 49 capes originals amb el mateix nom, mode, opacitat i visibilitat; les noves com cal
q = PSDImage.open(DST); L = list(q)
assert len(L) == n0 + 2, len(L)
src_l = list(PSDImage.open(SRC))
for a, b in zip(src_l, L[:n0]):
    assert (a.name, a.blend_mode, a.opacity, a.visible, a.bbox) == (b.name, b.blend_mode, b.opacity, b.visible, b.bbox), a.name
for nom, b in zip(noves, L[n0:]):
    assert b.name == nom and b.blend_mode == BlendMode.OVERLAY and not b.visible and abs(b.opacity - 51) <= 1, (b.name, b.blend_mode, b.opacity)
px = L[n0 + 1].numpy()                                           # la capa d'1° tal com la llegeix psd-tools (RGBA 0..1)
v1 = np.load(D / 'ls_1.0_v.npy')
dif = float(np.max(np.abs(px[..., 0] - np.clip(v1, 0, 1))[px[..., 3] > 0.5]))
info = dict(font=str(SRC.relative_to(A)), font_sha256=src_sha, desti=str(DST.relative_to(A)), desti_sha256=dst_sha,
            mida_GB=round(os.path.getsize(DST) / 1e9, 3), capes_originals=n0, capes_noves=noves,
            relectura=dict(capes=len(L), originals_iguals=True, dif_max_capa_1graus=dif), segons=round(time.time() - t0))
json.dump(info, open(D / 'LS2_PSB.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(info, indent=1, ensure_ascii=False))
