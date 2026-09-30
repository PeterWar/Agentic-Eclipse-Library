"""c9 · La cua de la protuberància esquerra de prop (3:1): el compost natiu desat (amb la marca de 175° i sense), i el compost emulat pis per pis:
base + filtres (on hi ha el detall fi de la protuberància), + Earthshine, + 76 (Aclarir, la foto curta), + 262 (Lluminositat). Sortida: LAMINA_M9_cua.png."""
from vm_comu import *
from psb69 import PSB
from vm_compost import comp, capa_box
import tifffile, io
from PIL import Image, ImageCms, ImageDraw, ImageFont
claim()
BP = (4760, 3600, 4960, 3860); x0, y0, x1, y1 = BP; h, w = y1 - y0, x1 - x0
p = PSB(str(PSB_PERE)); FILTRES = [41, 42, 47, 49, 51, 45, 46, 55, 56]
pisos = [('base + filtres', [3] + FILTRES), ('+ Earthshine 258', [258]), ('+ 76 foto (Aclarir)', [76]), ('+ 262 (Lluminositat)', [262]), ('+ 96 i 224', [96, 224])]
acc = []; res = {}
for nom, ids in pisos:
    acc += [capa_box(p, i, BP) for i in ids]; res[nom] = comp(acc, h, w)[0]
nat = p.composite()[y0:y1, x0:x1, :3]
z = np.load(SORT / 'marques_v88_crues.npz'); mo = z['origin']; mr = z['rgb'].astype(np.float32) / 65535; ma = z['alpha'].astype(np.float32) / 65535
amb = nat.astype(np.float32) / 65535; ys_, xs_ = mo[1] - y0, mo[0] - x0
Hm, Wm = ma.shape; ya, xa = max(ys_, 0), max(xs_, 0); yb, xb = min(ys_ + Hm, h), min(xs_ + Wm, w)
amb[ya:yb, xa:xb] = amb[ya:yb, xa:xb] * (1 - ma[ya - ys_:yb - ys_, xa - xs_:xb - xs_, None]) + mr[ya - ys_:yb - ys_, xa - xs_:xb - xs_] * ma[ya - ys_:yb - ys_, xa - xs_:xb - xs_, None]
icc = tifffile.TiffFile(V88D / 'vistes/V88_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
def im(C): return ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(C * 255, 0, 255))), TR)
try: F_ = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 19)
except Exception: F_ = FB = ImageFont.load_default()
panells = [('natiu desat amb la marca', amb), ('natiu desat', nat.astype(np.float32) / 65535)] + list(res.items())
zf = 3; S = Image.new('RGB', (4 * (w * zf + 8), 40 + 2 * (h * zf + 24)), 'white'); d = ImageDraw.Draw(S)
d.text((6, 8), 'Cua de la protuberància esquerra (3:1). Dalt: el compost natiu desat, amb la marca i sense, i els pisos emulats (sense capes d\'ajust)', fill='black', font=FB)
for i, (et, C) in enumerate(panells):
    r, c = divmod(i, 4); X = c * (w * zf + 8); Y = 40 + r * (h * zf + 24)
    S.paste(im(C).resize((w * zf, h * zf), Image.LANCZOS), (X, Y + 22)); d.text((X + 3, Y + 3), et, fill='black', font=F_)
S.save(SORT / 'LAMINA_M9_cua.png'); log('fet %s' % (S.size,))
