"""l_zoom · retall estret (8×) al voltant de la filera de punts, per variant, LANCZOS i nearest un al costat de l'altre."""
import sys; sys.path.insert(0, '/private/tmp/claude_v105/fila')
from comu_fila import *
from PIL import Image, ImageDraw
tag = sys.argv[1]; box = [int(v) for v in sys.argv[2].split(',')]; noms = sys.argv[3:]
CP = Compost(); V4 = CP.c()
tiles = [('V104', V4)] + [(n, np.load(OUT / n / 'COMP_emul.npy')) for n in noms]
a, b, c, d = box; Z = 8; rows = []
for t, arr in tiles:
    cr = arr[b - BOXL[1]:d - BOXL[1], a - BOXL[0]:c - BOXL[0]]; u = np.uint8(np.clip(cr, 0, 1) * 255 + 0.5)
    ims = [Image.fromarray(u).resize((cr.shape[1] * Z, cr.shape[0] * Z), f) for f in (Image.LANCZOS, Image.NEAREST)]
    cv = Image.new('RGB', (ims[0].width * 2 + 6, ims[0].height + 18), '#202020'); cv.paste(ims[0], (0, 18)); cv.paste(ims[1], (ims[0].width + 6, 18))
    ImageDraw.Draw(cv).text((4, 3), f'{t} · LANCZOS | nearest · {Z}x · {box}', fill='white'); rows.append(cv)
out = Image.new('RGB', (rows[0].width, sum(r.height + 4 for r in rows)), 'white'); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height + 4
out.save(OUT / 'laminas' / f'ZOOM_{tag}.png'); print(out.size)
