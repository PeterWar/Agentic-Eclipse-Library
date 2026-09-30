"""b5t · Làmina de totes les proves de la vora esquerra (compost de Photoshop, amb les capes d'ajust de Pere): la V88 de Pere amb la marca i
sense, B (només filtres), C (filtres que comencen on acaba la Lluna de Pere), D (la V88 exacta amb «Claridad y borrar neblina» oculta) i E (la B amb la claredat oculta).
Sortida: LAMINA_P6_totes_les_proves.png i LAMINA_P7_vora_esquerra_totes.png."""
from v89_comu import *
import tifffile, io
from PIL import Image, ImageCms, ImageDraw, ImageFont
claim()
VM = ARREL / '4-RESULTATS/v88_marques_pere_20260923'; B = (4600, 3000)
tf = tifffile.TiffFile(VM / 'compost_lluna.tif'); icc = tf.pages[0].tags['InterColorProfile'].value; V88 = tf.asarray()[..., :3]
P = {k: tifffile.imread(SORT / f'vistes/prova_{k}_lluna.tif')[..., :3] for k in 'BCDE'}
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
def im(a): return ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(a.astype(np.float32) / 257, 0, 255))), TR)
z = np.load(VM / 'marques_v88_crues.npz'); mo = z['origin']; mr = z['rgb'].astype(np.float32) / 65535; ma = z['alpha'].astype(np.float32) / 65535
amb = V88.astype(np.float32) / 65535; ys, xs = mo[1] - B[1], mo[0] - B[0]; sl = (slice(ys, ys + ma.shape[0]), slice(xs, xs + ma.shape[1]))
amb[sl] = amb[sl] * (1 - ma[..., None]) + mr * ma[..., None]; amb = np.round(amb * 65535).astype(np.uint16)
geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
M = json.loads((VM / 'MARQUES_V88.json').read_text()); llocs = [(g['nom'], cc) for g in M['grups_de_to'] for cc in g['components']]
try: F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 14); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 19)
except Exception: F = FB = ImageFont.load_default()
cols = [(amb, 'V88 amb la marca'), (V88, 'V88 (ara)'), (P['B'], 'B · filtres sense pujada'), (P['C'], 'C · B + comencen on acaba la teva Lluna'), (P['D'], 'D · V88 sense «Claridad»'), (P['E'], 'E · B sense «Claridad»')]
w, zf = 100, 4; S = Image.new('RGB', (len(cols) * (w * zf + 8), 40 + len(llocs) * (w * zf + 24)), 'white'); d = ImageDraw.Draw(S)
d.text((6, 8), "Totes les proves de la vora esquerra, compost de Photoshop (amb les teves capes d'ajust), 4:1", fill='black', font=FB)
for j, (nom, cc) in enumerate(llocs):
    az, dm = cc['azimut'][1], cc['d_limbe_px'][1]; t = np.radians(az); px, py = cx + (R + dm) * np.cos(t) - B[0], cy - (R + dm) * np.sin(t) - B[1]
    x0, y0 = int(px - w / 2), int(py - w / 2); Y = 40 + j * (w * zf + 24)
    for i, (arr, et) in enumerate(cols):
        S.paste(im(arr[y0:y0 + w, x0:x0 + w]).resize((w * zf, w * zf), Image.LANCZOS), (i * (w * zf + 8), Y + 20)); d.text((i * (w * zf + 8) + 3, Y + 2), f'{et} · {az:.0f}°', fill='black', font=F)
S.save(SORT / 'LAMINA_P6_totes_les_proves.png')
BV = (4840 - B[0], 3380 - B[1], 5090 - B[0], 4180 - B[1]); zz = 2; ww, hh = (BV[2] - BV[0]) * zz, (BV[3] - BV[1]) * zz
S2 = Image.new('RGB', (5 * (ww + 8), hh + 36), 'white'); d2 = ImageDraw.Draw(S2)
for i, (arr, et) in enumerate(cols[1:]):
    S2.paste(im(arr[BV[1]:BV[3], BV[0]:BV[2]]).resize((ww, hh), Image.LANCZOS), (i * (ww + 8), 34)); d2.text((i * (ww + 8) + 4, 8), et, fill='black', font=FB)
S2.save(SORT / 'LAMINA_P7_vora_esquerra_totes.png'); log('làmines fetes')
