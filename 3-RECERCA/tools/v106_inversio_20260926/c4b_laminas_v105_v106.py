"""c4b (V106) · Làmines 4:1 del compost EMULAT (sense les capes d'ajust de Pere): V105 | V106 | diferència (×8, gris = cap canvi), a sis punts del limbe.
Ús: c4b_laminas_v105_v106.py <carpeta amb COMP_V105_emul.npy i COMP_V106_emul.npy> <etiqueta>"""
import sys, numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
folder = Path(sys.argv[1]); tag = sys.argv[2]; bx0, by0 = 4677, 3077
V5 = np.load(folder / 'COMP_V105_emul.npy'); V6 = np.load(folder / 'COMP_V106_emul.npy')
coords = {'dalt': (5246, 3283, 5506, 3413), 'dalt_esquerra': (4986, 3386, 5126, 3526), 'esquerra': (4853, 3706, 4993, 3846), 'baix_esquerra': (4986, 4026, 5126, 4166),
          'baix': (5246, 4189, 5506, 4319), 'baix_dreta': (5620, 4026, 5760, 4166), 'dreta': (5759, 3706, 5899, 3846)}
for nm, (a, b, c, d) in coords.items():
    ims = []
    dif = 0.5 + 8 * (V6 - V5)
    for t, arr in [('V105 (emulada, sense ajustos)', V5), ('V106 (emulada, sense ajustos)', V6), ('V106 - V105 (x8)', dif)]:
        cr = arr[b - by0:d - by0, a - bx0:c - bx0]; im = Image.fromarray(np.uint8(np.clip(cr, 0, 1) * 255)).resize(((c - a) * 4, (d - b) * 4), Image.NEAREST)
        cv = Image.new('RGB', (im.width, im.height + 22), '#202020'); cv.paste(im, (0, 22)); ImageDraw.Draw(cv).text((6, 5), t, fill='white'); ims.append(cv)
    out = Image.new('RGB', (sum(i.width for i in ims) + 12, ims[0].height), 'white'); x = 0
    for i in ims: out.paste(i, (x, 0)); x += i.width + 6
    out.save(folder / f'COMP4_{tag}_{nm}.png')
print('ok')
