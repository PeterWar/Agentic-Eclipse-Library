"""Congela, fora del PSB de 9,6 GB, el que la V35 (i tota versió lleugera) necessita de V32.psb: per a cada una de les 10
capes de filtre, alfa, màscara (amb la seva caixa i color de fons), mode, opacitat i visibilitat. Sortida: frozen/modes_mascares_v32.npz
(comprimit) + modes_mascares_v32.json (estadístiques i hashes) perquè un replicador no depengui del PSB sencer."""
import sys, json, hashlib, zlib
from pathlib import Path
import numpy as np
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026'); sys.path.insert(0, str(ROOT / 'research/tools/v29')); sys.path.insert(0, str(ROOT / 'research/tools/encaix_sony'))
from inspect_inputs import channel, sha
from psd_tools import PSDImage
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals'); FONT = CT / 'V32.psb'; FONT_SHA = 'dcfc8f531e286bfdf529d20880c9772785a38a4e6d0c09094883a7c8f7743c7d'
NAMES = ['01 ACHF fi 2-32 · V32', '02 Passa-alt 24 · V32', '04 ACHF micro 1-16 · V32', '05 ACHF fi 2-48 · V32', '06 ACHF estructura 4-64 · V32', 'P01 NRGF · V32', 'P02 RHEF · comparacio amb anells · V32', 'P03 MGN · V32', 'P04 WOW sense denoise · V32', 'P05 WOW bilateral sense denoise · V32']
OUT = Path(__file__).resolve().parent
assert sha(FONT) == FONT_SHA
s = PSDImage.open(FONT); by = {l.name: l for l in s}; arrays = {}; meta = {'font': str(FONT), 'font_sha256': FONT_SHA, 'capes': []}
for n in NAMES:
    l = by[n]; a = channel(l, -1); md = l._record.mask_data; m = channel(l, -2) if md is not None else None
    key = n.split(' ')[0]; arrays[f'{key}_alpha'] = a
    row = {'name': n, 'key': key, 'blend': l.blend_mode.name, 'opacity': int(l.opacity), 'visible': bool(l.visible), 'alpha_sha256': hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest(), 'alpha_min_max_mean': [int(a.min()), int(a.max()), float(a.mean())]}
    if m is not None:
        arrays[f'{key}_mask'] = m; row.update({'mask_box_ltrb': [md.left, md.top, md.right, md.bottom], 'mask_background': int(md.background_color), 'mask_sha256': hashlib.sha256(np.ascontiguousarray(m).tobytes()).hexdigest(), 'mask_min_max_mean': [int(m.min()), int(m.max()), float(m.mean())], 'mask_frac_65535': float(np.mean(m == 65535))})
    meta['capes'].append(row); print(row['key'], row['blend'], row['opacity'], row['visible'], row['alpha_min_max_mean'], row.get('mask_min_max_mean'), row.get('mask_frac_65535'), flush=True)
np.savez_compressed(OUT / 'modes_mascares_v32.npz', **arrays); meta['npz_sha256'] = sha(OUT / 'modes_mascares_v32.npz'); meta['npz_bytes'] = (OUT / 'modes_mascares_v32.npz').stat().st_size
(OUT / 'modes_mascares_v32.json').write_text(json.dumps(meta, indent=1, ensure_ascii=False) + '\n'); print('npz', meta['npz_bytes'], meta['npz_sha256'])
