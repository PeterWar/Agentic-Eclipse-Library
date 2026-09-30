"""c9 · Làmina EMULADA a 6:1 de les variants de la vora a les línies de la V88 i a les marques verdes: V88, V92, V93 (VORA 2, σ 12) i V93 (VORA 2, σ 24)."""
from v93_comu import *
from psb69 import PSB
from vm_compost import comp, capa_box
import tifffile, io
from PIL import Image, ImageCms, ImageDraw, ImageFont
claim(); BX = (4600, 3000, 6150, 4550); W_, H_ = BX[2] - BX[0], BX[3] - BX[1]; cx, cy, R = GEO['cx'] - BX[0], GEO['cy'] - BX[1], GEO['R']
VAR = {'V88': ARREL / '4-RESULTATS/v88_20260923/filtres_finals', 'V92': ARREL / '4-RESULTATS/v92_20260924/filtres_v92', 'V93 σ12': SORT / 'prova_v2_s12', 'V93 σ24': SORT / 'prova_v2_s24'}
p = PSB(str(PSB_PERE)); vis = [L['id'] for L in p.layers if L['visible'] and L['right'] > L['left'] and L['id'] not in (239, 240, 241, 242, 243, 244, 269)]
CAPES = {i: capa_box(p, i, BX) for i in vis}; COMP = {}
for nm, carp in VAR.items():
    capes = []
    for i in vis:
        if i in FILTRES: md, F_, a_ = CAPES[i]; v = np.load(carp / f'{FILTRES[i]}_u16.npy', mmap_mode='r')[BX[1]:BX[3], BX[0]:BX[2]].astype(np.float32) / 65535; capes.append((md, np.repeat(v[..., None], 3, -1), a_))
        else: capes.append(CAPES[i])
    COMP[nm] = comp(capes, H_, W_)[0]
icc = tifffile.TiffFile(ARREL / '4-RESULTATS/v92_20260924/vistes/V92_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB'); im = lambda A: ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(A * 255, 0, 255))), TR)
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
files = [(112, 5), (136, 5), (211, 5), (223, 5), (200, 8), (219, 6)]; w, zf = 60, 6
S = Image.new('RGB', (len(COMP) * (w * zf + 8), len(files) * (w * zf + 24)), 'white'); d = ImageDraw.Draw(S)
for j, (az, dm) in enumerate(files):
    tt = np.radians(az); px, py = cx + (R + dm) * np.cos(tt), cy - (R + dm) * np.sin(tt); x0, y0 = int(px - w / 2), int(py - w / 2); Y0 = j * (w * zf + 24)
    for i, n in enumerate(COMP): S.paste(im(COMP[n][y0:y0 + w, x0:x0 + w]).resize((w * zf, w * zf), Image.LANCZOS), (i * (w * zf + 8), Y0 + 20)); d.text((i * (w * zf + 8) + 3, Y0 + 2), f'{n} · {az:.0f}°', fill='black', font=F)
S.save(SORT / 'LAMINA_C9_variants.png'); log('fet')
