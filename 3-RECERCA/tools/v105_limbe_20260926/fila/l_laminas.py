"""l_laminas · làmines 6× (LANCZOS i nearest) a dalt, dalt-esquerra i baix-esquerra: foto 09 1/60 x2 de Pere (capa 303), V104 emulada i variants.
Ús: l_laminas.py <etiqueta> <variant> [<variant> ...]"""
import sys; sys.path.insert(0, '/private/tmp/claude_v105/fila')
from comu_fila import *
from PIL import Image, ImageDraw
tag = sys.argv[1]; noms = sys.argv[2:]
CP = Compost(); V4 = CP.c()
ref = np.load('/private/tmp/eclipse_v104_diagnosi_20260926/L303.npz'); r3 = np.stack([ref['c%d' % c] for c in range(3)], -1).astype(np.float32) / 65535; r3 = r3[77:1477, 77:1477]
CROPS = {'dalt': (5300, 3300, 5420, 3350), 'dalt_esq': (5020, 3380, 5100, 3440), 'baix_esq': (5020, 4110, 5100, 4170)}
tiles = [('09 1/60 x2 (Pere, capa 303)', r3), ('V104 emulada', V4)] + [(n, np.load(OUT / n / 'COMP_emul.npy')) for n in noms]
Z = 6; (OUT / 'laminas').mkdir(exist_ok=True)
for filt, fn in (('lanczos', Image.LANCZOS), ('nearest', Image.NEAREST)):
    for cn, (a, b, c, d) in CROPS.items():
        ims = []
        for t, arr in tiles:
            cr = arr[b - BOXL[1]:d - BOXL[1], a - BOXL[0]:c - BOXL[0]]
            im = Image.fromarray(np.uint8(np.clip(cr, 0, 1) * 255 + 0.5)).resize((cr.shape[1] * Z, cr.shape[0] * Z), fn)
            cv = Image.new('RGB', (im.width, im.height + 20), '#202020'); cv.paste(im, (0, 20)); ImageDraw.Draw(cv).text((4, 4), f'{t} · {cn} · {filt} {Z}x', fill='white'); ims.append(cv)
        Wd = ims[0].width; Ht = sum(i.height + 4 for i in ims); out = Image.new('RGB', (Wd, Ht), 'white'); y = 0
        for i in ims: out.paste(i, (0, y)); y += i.height + 4
        out.save(OUT / 'laminas' / f'{tag}_{cn}_{filt}.png')
print('ok', tag)
