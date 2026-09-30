"""c6b · Avaluació de les variants de c6a al compost EMULAT de la V91 de Pere (00:14), canviant només el ràster de la 56:
índex de lent per sector (c1/c5), perfil del nivell mitjà arran del limbe (per veure si surt cap vora clara o fosca nova) i làmina a 4:1 a les
marques roses de la V90 i a les línies de la V88. Sortida: C6B_AVALUACIO.json, LAMINA_C6_lent_4a1.png i LAMINA_C6_linies_4a1.png."""
from pathlib import Path
import json, sys, io
import numpy as np, cv2, tifffile
from scipy.ndimage import gaussian_filter1d, uniform_filter1d
from PIL import Image, ImageCms, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v91_lent_residual_20260923'; PR = SORT / 'prova_mirall'
for p_ in ('v73_marques_v71_20260917', 'v86_neta_20260923', 'v90_marques_pere_20260923'): sys.path.insert(0, str(ARREL / '3-RECERCA/tools' / p_))
from psb69 import PSB
from vm_compost import comp, capa_box
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
GEO = json.loads((ARREL / '4-RESULTATS/v91_20260923/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; BX = (4600, 3000, 6150, 4550); W_, H_ = BX[2] - BX[0], BX[3] - BX[1]
cx, cy, R = GEO['cx'] - BX[0], GEO['cy'] - BX[1], GEO['R']
DT = 0.05; NT = int(360 / DT); DR = 0.25; DS = np.arange(-3, 30.001, DR); TS = np.radians((np.arange(NT) + 0.5) * DT)
TT, DD = np.meshgrid(TS, DS); MX = (cx + (R + DD) * np.cos(TT)).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT)).astype(np.float32)
ds_arc = np.radians(DT) * (R + DS)[:, None]; near = (DS >= 2.5) & (DS <= 10); far = (DS >= 16) & (DS <= 30); t = np.arange(NT) * DT
SECT = {'rosa_0_32': [(0, 32), (352, 360)], 'rosa_45_98': [(45, 98)], 'rosa_230_305': [(230, 305)], 'esquerra_120_220': [(120, 220)]}
sel = lambda v: np.concatenate([np.flatnonzero((t >= a) & (t < b)) for a, b in v])
def pol(Y): return cv2.remap(Y.astype(np.float32), MX, MY, cv2.INTER_LINEAR)
def index(Y, prop=near):
    P = pol(Y); T = P - gaussian_filter1d(P, 3.0 / ds_arc.mean(), axis=1, mode='wrap')
    Ed = (np.diff(T, axis=0) / DR) ** 2; Ed = np.vstack([Ed, Ed[-1:]]); Es = (np.diff(T, axis=1, append=T[:, :1]) / ds_arc) ** 2
    Wn = int(5 / DT); f = lambda E, mk: uniform_filter1d(E[mk].mean(0), Wn, mode='wrap'); L = (f(Ed, far) / f(Es, far)) / (f(Ed, prop) / f(Es, prop))
    return {k: round(float(L[sel(v)].mean()), 2) for k, v in SECT.items()}
def perfil(Y):
    P = pol(Y); return {k: [round(float(P[np.abs(DS - d) < 0.3][:, sel(v)].mean()), 4) for d in (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20)] for k, v in SECT.items()}
lum = lambda C: 0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2]
p = PSB(str(ARREL / '1-PHOTOSHOP/V91.psb')); vis = [L['id'] for L in p.layers if L['visible'] and L['right'] > L['left'] and L['id'] not in (239, 240, 241, 242, 243, 244)]
CAPES = {i: capa_box(p, i, BX) for i in vis}; mode56, F56, a56 = CAPES[56]; rep = {'raster_56': {}, 'compost': {}, 'perfil_compost': {}}; COMP = {}
for nom in ('actual', 'A_a4_mirall', 'B_wow_mirall', 'C_tots_dos'):
    v = np.load(PR / f'{nom}_u16.npy', mmap_mode='r')[BX[1]:BX[3], BX[0]:BX[2]].astype(np.float32) / 65535
    rep['raster_56'][nom] = dict(lent_2_10=index(v), lent_1_5=index(v, (DS >= 1) & (DS <= 5)), lent_5_14=index(v, (DS >= 5) & (DS <= 14)))
    capes = [CAPES[i] if i != 56 else (mode56, np.repeat(v[..., None], 3, -1), a56) for i in vis]; C = comp(capes, H_, W_)[0]; COMP[nom] = C
    rep['compost'][nom] = dict(lent_2_10=index(lum(C)), lent_1_5=index(lum(C), (DS >= 1) & (DS <= 5)), lent_5_14=index(lum(C), (DS >= 5) & (DS <= 14))); rep['perfil_compost'][nom] = perfil(lum(C))
    print(nom, 'ràster 56:', json.dumps(rep['raster_56'][nom]), '\n    compost:', json.dumps(rep['compost'][nom]), flush=True)
for k in SECT: print('perfil del nivell (compost) a', k, {n: rep['perfil_compost'][n][k] for n in COMP}, flush=True)
(SORT / 'C6B_AVALUACIO.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n')
icc = tifffile.TiffFile(ARREL / '4-RESULTATS/v88_marques_pere_20260923/compost_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
im = lambda A: ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(A * 255, 0, 255))), TR)
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 18)
def lamina(nom, titol, files, w=90, zf=4):
    cols = list(COMP); S = Image.new('RGB', (len(cols) * (w * zf + 8), 40 + len(files) * (w * zf + 24)), 'white'); d = ImageDraw.Draw(S); d.text((6, 8), titol, fill='black', font=FB)
    for j, (az, dm) in enumerate(files):
        tt = np.radians(az); px, py = cx + (R + dm) * np.cos(tt), cy - (R + dm) * np.sin(tt); x0, y0 = int(px - w / 2), int(py - w / 2); Y0 = 40 + j * (w * zf + 24)
        for i, n in enumerate(cols):
            S.paste(im(COMP[n][y0:y0 + w, x0:x0 + w]).resize((w * zf, w * zf), Image.LANCZOS), (i * (w * zf + 8), Y0 + 20)); d.text((i * (w * zf + 8) + 3, Y0 + 2), f'{n} · {az:.0f}°', fill='black', font=F)
    S.save(SORT / nom)
lamina('LAMINA_C6_lent_4a1.png', 'Prova del mirall (compost EMULAT, sense capes d\'ajust), a les marques roses de la V90, 4:1', [(8, 6), (26, 5), (55, 6), (80, 6), (240, 8), (262, 8), (285, 8), (300, 8)])
lamina('LAMINA_C6_linies_4a1.png', 'Prova del mirall (compost EMULAT), a les línies de la V88 (no han de tornar), 4:1', [(112, 5), (136, 5), (211, 5), (223, 5)])
print('fet')
