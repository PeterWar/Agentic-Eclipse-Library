"""c2 · El compost natiu de la V88 de Pere (la imatge fusionada que Photoshop desa dins del PSB, amb les capes d'ajust incloses) i les seves marques.
El document obert a Photoshop és el mateix que el del disc (desat=true, 38 capes): no cal tocar Photoshop.
Sortida: compost_lluna.tif (caixa 4600..6150 × 3000..4550, uint16, ICC del document), LAMINA_M1_marques.png (cada marca a 4:1, amb i sense la marca)."""
from vm_comu import *
from psb69 import PSB
import tifffile, io, cv2
from PIL import Image, ImageCms, ImageDraw, ImageFont
claim()
B = (4600, 3000, 6150, 4550)
p = PSB(str(PSB_PERE)); comp = p.composite(); log('compost %s' % (comp.shape,))
icc = tifffile.TiffFile(V88D / 'vistes/V88_lluna.tif').pages[0].tags['InterColorProfile'].value
c = np.ascontiguousarray(comp[B[1]:B[3], B[0]:B[2], :3])
tifffile.imwrite(SORT / 'compost_lluna.tif', c, photometric='rgb', iccprofile=icc, compression='zlib')
tifffile.imwrite(SORT / 'compost_llenc_sencer_quart.tif', np.ascontiguousarray(comp[::4, ::4, :3]), photometric='rgb', iccprofile=icc, compression='zlib')
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
def im16(a): return ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(a.astype(np.float32) / 257, 0, 255))), TR)
z = np.load(SORT / 'marques_v88_crues.npz'); mo = z['origin']; mr = z['rgb'].astype(np.float32) / 65535; ma = z['alpha'].astype(np.float32) / 65535
amb = c.astype(np.float32) / 65535; ys, xs = mo[1] - B[1], mo[0] - B[0]; sl = (slice(ys, ys + ma.shape[0]), slice(xs, xs + ma.shape[1]))
amb[sl] = amb[sl] * (1 - ma[..., None]) + mr * ma[..., None]; amb = np.uint16(np.round(amb * 65535))
M = json.loads((SORT / 'MARQUES_V88.json').read_text()); cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
try: F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 19)
except Exception: F = FB = ImageFont.load_default()
llocs = [(g['nom'], cc) for g in M['grups_de_to'] for cc in g['components']]
w, zf = 110, 4; S = Image.new('RGB', (3 * (w * zf + 8), 40 + len(llocs) * (w * zf + 26)), 'white'); d = ImageDraw.Draw(S)
d.text((6, 8), 'Marques de la capa Artefactes V88 sobre el compost natiu desat (4:1): amb la marca · sense · sense amb els foscos aixecats (x3)', fill='black', font=FB)
for j, (nom, cc) in enumerate(llocs):
    az = cc['azimut'][1]; dm = cc['d_limbe_px'][1]; t = np.radians(az)
    px, py = cx + (R + dm) * np.cos(t) - B[0], cy - (R + dm) * np.sin(t) - B[1]; x0, y0 = int(px - w / 2), int(py - w / 2); y = 40 + j * (w * zf + 26)
    for i, (arr, et) in enumerate([(amb, 'amb la marca'), (c, 'compost natiu'), (np.clip(c.astype(np.float32) * 3, 0, 65535), 'foscos x3')]):
        S.paste(im16(arr[y0:y0 + w, x0:x0 + w]).resize((w * zf, w * zf), Image.LANCZOS), (i * (w * zf + 8), y + 22))
        d.text((i * (w * zf + 8) + 3, y + 3), f'{et} · {nom} · az {az:.0f}° · d {dm:+.0f} px', fill='black', font=F)
S.save(SORT / 'LAMINA_M1_marques.png'); log('làmina M1 %s' % (S.size,))
