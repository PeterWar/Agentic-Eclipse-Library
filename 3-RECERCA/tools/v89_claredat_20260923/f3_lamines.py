"""f3 · Làmines de la prova F (claredat amb màscara radial), totes amb compost de Photoshop: V88 de Pere, D (V88 sense la claredat) i F (claredat
fora de la Lluna i de 18 px al voltant del limbe, fosa fins a 36 px). 1) cada marca a 4:1; 2) la Lluna sencera a 2:3 (per veure la transició de
18–36 px al voltant); 3) el llenç sencer V88 contra F. Sortida: LAMINA_F1_marques.png, LAMINA_F2_lluna.png, LAMINA_F3_llenc.png."""
from pathlib import Path
import json, io, numpy as np, tifffile
from PIL import Image, ImageCms, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v89_claredat_20260923'; VM = ARREL / '4-RESULTATS/v88_marques_pere_20260923'
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
B = (4600, 3000); tf = tifffile.TiffFile(VM / 'compost_lluna.tif'); icc = tf.pages[0].tags['InterColorProfile'].value; V88 = tf.asarray()[..., :3]
PD = tifffile.imread(ARREL / '4-RESULTATS/v89_proves_20260923/vistes/prova_D_lluna.tif')[..., :3]; PF = tifffile.imread(SORT / 'vistes/prova_F_lluna.tif')[..., :3]
assert V88.shape == PD.shape == PF.shape
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
def im(a): return ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(a.astype(np.float32) / 257, 0, 255))), TR)
z = np.load(VM / 'marques_v88_crues.npz'); mo = z['origin']; mr = z['rgb'].astype(np.float32) / 65535; ma = z['alpha'].astype(np.float32) / 65535
amb = V88.astype(np.float32) / 65535; ys, xs = mo[1] - B[1], mo[0] - B[0]; sl = (slice(ys, ys + ma.shape[0]), slice(xs, xs + ma.shape[1]))
amb[sl] = amb[sl] * (1 - ma[..., None]) + mr * ma[..., None]; amb = np.round(amb * 65535).astype(np.uint16)
geo = json.loads((ARREL / '4-RESULTATS/v88_20260923/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
M = json.loads((VM / 'MARQUES_V88.json').read_text()); llocs = [(g['nom'], cc) for g in M['grups_de_to'] for cc in g['components']]
try: F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 19)
except Exception: F = FB = ImageFont.load_default()
cols = [(amb, 'V88 amb la marca'), (V88, 'V88 (ara)'), (PD, 'D · sense claredat'), (PF, 'F · claredat amb màscara radial')]
w, zf = 110, 4; S = Image.new('RGB', (len(cols) * (w * zf + 8), 40 + len(llocs) * (w * zf + 26)), 'white'); d = ImageDraw.Draw(S)
d.text((6, 8), "Claredat amb màscara radial (prova F), compost de Photoshop, 4:1", fill='black', font=FB)
for j, (nom, cc) in enumerate(llocs):
    az, dm = cc['azimut'][1], cc['d_limbe_px'][1]; t = np.radians(az); px, py = cx + (R + dm) * np.cos(t) - B[0], cy - (R + dm) * np.sin(t) - B[1]
    x0, y0 = int(px - w / 2), int(py - w / 2); Y = 40 + j * (w * zf + 26)
    for i, (arr, et) in enumerate(cols):
        S.paste(im(arr[y0:y0 + w, x0:x0 + w]).resize((w * zf, w * zf), Image.LANCZOS), (i * (w * zf + 8), Y + 22)); d.text((i * (w * zf + 8) + 3, Y + 3), f'{et} · {az:.0f}°', fill='black', font=F)
S.save(SORT / 'LAMINA_F1_marques.png')
k = 1024; S2 = Image.new('RGB', (3 * (k + 8), k + 36), 'white'); d2 = ImageDraw.Draw(S2)
for i, (arr, et) in enumerate(cols[1:]):
    S2.paste(im(arr).resize((k, k), Image.LANCZOS), (i * (k + 8), 34)); d2.text((i * (k + 8) + 4, 8), 'Lluna 2:3 · ' + et, fill='black', font=FB)
S2.save(SORT / 'LAMINA_F2_lluna.png')
L88 = tifffile.imread(VM / 'compost_llenc_sencer_quart.tif')[..., :3]; LF = tifffile.imread(SORT / 'vistes/prova_F_llenc.tif')[..., :3]
a1 = im(L88); a2 = im(LF).resize(a1.size, Image.LANCZOS); ww = 1400; hh = round(a1.height * ww / a1.width)
S3 = Image.new('RGB', (2 * (ww + 8), hh + 36), 'white'); d3 = ImageDraw.Draw(S3)
for i, (a, et) in enumerate([(a1, 'V88 (ara) · llenç sencer'), (a2, 'F · claredat amb màscara radial · llenç sencer')]):
    S3.paste(a.resize((ww, hh), Image.LANCZOS), (i * (ww + 8), 34)); d3.text((i * (ww + 8) + 4, 8), et, fill='black', font=FB)
S3.save(SORT / 'LAMINA_F3_llenc.png'); print('làmines fetes')
