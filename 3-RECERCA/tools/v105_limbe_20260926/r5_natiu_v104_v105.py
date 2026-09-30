"""r5 (V105) · Compara el render natiu de la V105 (amb les capes d'ajust de Pere) amb el de la V104: on canvia, retalls nous i làmines 4:1
09 (capa 303 de Pere) | V104 | V105 als sis llocs de les comparacions del Codex. Ús: r5_natiu_v104_v105.py <V104_lluna.tif> <V105_lluna.tif> <sortida>"""
import sys, json, numpy as np, tifffile
from pathlib import Path
from PIL import Image, ImageDraw
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
A = tifffile.imread(sys.argv[1])[..., :3].astype(np.int32); B = tifffile.imread(sys.argv[2])[..., :3].astype(np.int32); O = Path(sys.argv[3]); O.mkdir(parents=True, exist_ok=True)
cx, cy, R = 5375.786804312011, 3775.9774911631, 452.9785129274736; x0, y0 = 4600, 3000
yy, xx = np.mgrid[y0:y0 + A.shape[0], x0:x0 + A.shape[1]]; d = np.hypot(xx - cx, yy - cy) - R
D = np.abs(B - A).max(-1)
rep = dict(pixels_diferents=int((D > 0).sum()), pixels_dif_256=int((D > 256).sum()), dif_max=int(D.max()), dif_max_fora_banda=int(D[(d < -4) | (d > 16)].max()),
           d_dels_canvis_64=[float(v) for v in np.percentile(d[D > 64], [0, 1, 50, 99, 100])] if (D > 64).any() else None,
           retalls={n: dict(V104=int((A[..., c] == 65535).sum()), V105=int((B[..., c] == 65535).sum()), nous=int(((B[..., c] == 65535) & (A[..., c] < 65535)).sum())) for c, n in enumerate('RGB')})
p = PSB(str(ARREL / '1-PHOTOSHOP/V104.psb')); a, (ox, oy) = p.channel(303, 0)[0], p.channel(303, 0)[1]
ref = np.zeros(A.shape, np.uint16)
for c in range(3):
    ch, (ox, oy) = p.channel(303, c); ref[..., c] = ch[y0 - oy:y0 - oy + A.shape[0], x0 - ox:x0 - ox + A.shape[1]]
coords = {'dalt': (646, 283, 906, 413), 'dalt_esquerra': (386, 386, 526, 526), 'esquerra': (253, 706, 393, 846), 'baix_esquerra': (386, 1026, 526, 1166), 'baix': (646, 1189, 906, 1319), 'dreta': (1159, 706, 1299, 846)}
for nm, (a_, b_, c_, e_) in coords.items():
    ims = []
    for arr, t in ((ref, 'Capa 09 1/60 x2 · Pere'), (A, 'V104 · render natiu'), (B, 'V105 · render natiu')):
        im = Image.fromarray((np.clip(arr[b_:e_, a_:c_], 0, 65535) / 257).astype(np.uint8)).resize(((c_ - a_) * 4, (e_ - b_) * 4), Image.NEAREST)
        cv = Image.new('RGB', (im.width, im.height + 30), '#202020'); cv.paste(im, (0, 30)); ImageDraw.Draw(cv).text((8, 8), t, fill='white'); ims.append(cv)
    out = Image.new('RGB', (sum(i.width for i in ims) + 24, ims[0].height), 'white'); x = 0
    for i in ims: out.paste(i, (x, 0)); x += i.width + 12
    out.save(O / f'NATIU_{nm}_09_V104_V105_4a1.png')
(O / 'R5_NATIU.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False))
