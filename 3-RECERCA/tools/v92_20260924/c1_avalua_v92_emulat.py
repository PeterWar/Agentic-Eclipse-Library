"""c1 (V92) · Els 16 filtres de la V92 (mirall + a5c) contra els de la V91, al compost EMULAT de la V91 de Pere (00:14): índex de lent per sector
i banda, perfil del nivell arran del limbe i làmines a 4:1 (marques roses de la V90 i línies de la V88). Sortida: C1_AVALUACIO.json i LAMINA_C1_*.png."""
from pathlib import Path
import json, sys, io
import numpy as np, cv2, tifffile
from scipy.ndimage import gaussian_filter1d, uniform_filter1d
from PIL import Image, ImageCms, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v92_20260924'
for p_ in ('v73_marques_v71_20260917', 'v86_neta_20260923', 'v90_marques_pere_20260923'): sys.path.insert(0, str(ARREL / '3-RECERCA/tools' / p_))
from psb69 import PSB
from vm_compost import comp, capa_box
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
FILTRES = {48: '03v30', 50: '01', 52: '05', 53: '06', 54: 'P03_MGN', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap',
           47: '03', 49: '07', 51: '04', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
GEO = json.loads((ARREL / '4-RESULTATS/v91_20260923/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; BX = (4600, 3000, 6150, 4550); W_, H_ = BX[2] - BX[0], BX[3] - BX[1]
cx, cy, R = GEO['cx'] - BX[0], GEO['cy'] - BX[1], GEO['R']
DT = 0.05; NT = int(360 / DT); DR = 0.25; DS = np.arange(-3, 30.001, DR); TS = np.radians((np.arange(NT) + 0.5) * DT)
TT, DD = np.meshgrid(TS, DS); MX = (cx + (R + DD) * np.cos(TT)).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT)).astype(np.float32)
ds_arc = np.radians(DT) * (R + DS)[:, None]; far = (DS >= 16) & (DS <= 30); t = np.arange(NT) * DT
SECT = {'rosa_0_32': [(0, 32), (352, 360)], 'rosa_45_98': [(45, 98)], 'rosa_230_305': [(230, 305)], 'esquerra_104_228': [(104, 228)], 'dreta_305_352': [(305, 352)]}
BANDES = {'1-5': (1, 5), '5-14': (5, 14), '2.5-10': (2.5, 10)}
sel = lambda v: np.concatenate([np.flatnonzero((t >= a) & (t < b)) for a, b in v])
def pol(Y): return cv2.remap(Y.astype(np.float32), MX, MY, cv2.INTER_LINEAR)
def index(Y):
    P = pol(Y); T = P - gaussian_filter1d(P, 3.0 / ds_arc.mean(), axis=1, mode='wrap')
    Ed = (np.diff(T, axis=0) / DR) ** 2; Ed = np.vstack([Ed, Ed[-1:]]); Es = (np.diff(T, axis=1, append=T[:, :1]) / ds_arc) ** 2
    Wn = int(5 / DT); f = lambda E, mk: uniform_filter1d(E[mk].mean(0), Wn, mode='wrap'); out = {}
    for bn, (a, b) in BANDES.items():
        mk = (DS >= a) & (DS <= b); L = (f(Ed, far) / f(Es, far)) / (f(Ed, mk) / f(Es, mk)); out[bn] = {k: round(float(L[sel(v)].mean()), 2) for k, v in SECT.items()}
    return out
def perfil(Y): P = pol(Y); return {k: [round(float(P[np.abs(DS - d) < 0.3][:, sel(v)].mean()), 4) for d in (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20)] for k, v in SECT.items()}
lum = lambda C: 0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2]
p = PSB(str(ARREL / '1-PHOTOSHOP/V91.psb')); vis = [L['id'] for L in p.layers if L['visible'] and L['right'] > L['left'] and L['id'] not in (239, 240, 241, 242, 243, 244)]
CAPES = {i: capa_box(p, i, BX) for i in vis}; COMP = {'V91': comp([CAPES[i] for i in vis], H_, W_)[0]}
capes = []
for i in vis:
    if i in FILTRES:
        md, F_, a_ = CAPES[i]; v = np.load(SORT / 'filtres_v92' / f'{FILTRES[i]}_u16.npy', mmap_mode='r')[BX[1]:BX[3], BX[0]:BX[2]].astype(np.float32) / 65535
        capes.append((md, np.repeat(v[..., None], 3, -1), a_))
    else: capes.append(CAPES[i])
COMP['V92'] = comp(capes, H_, W_)[0]
rep = {n: dict(index=index(lum(C)), perfil=perfil(lum(C))) for n, C in COMP.items()}
for n in COMP: print(n, json.dumps(rep[n]['index']), flush=True)
for k in SECT: print('nivell', k, 'V91', rep['V91']['perfil'][k], '\n       V92', rep['V92']['perfil'][k], flush=True)
(SORT / 'C1_AVALUACIO.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n')
icc = tifffile.TiffFile(ARREL / '4-RESULTATS/v88_marques_pere_20260923/compost_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
im = lambda A: ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(A * 255, 0, 255))), TR)
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 18)
def lamina(nom, titol, files, w=80, zf=5):
    S = Image.new('RGB', (2 * (w * zf + 8), 40 + len(files) * (w * zf + 24)), 'white'); d = ImageDraw.Draw(S); d.text((6, 8), titol, fill='black', font=FB)
    for j, (az, dm) in enumerate(files):
        tt = np.radians(az); px, py = cx + (R + dm) * np.cos(tt), cy - (R + dm) * np.sin(tt); x0, y0 = int(px - w / 2), int(py - w / 2); Y0 = 40 + j * (w * zf + 24)
        for i, n in enumerate(COMP):
            S.paste(im(COMP[n][y0:y0 + w, x0:x0 + w]).resize((w * zf, w * zf), Image.LANCZOS), (i * (w * zf + 8), Y0 + 20)); d.text((i * (w * zf + 8) + 3, Y0 + 2), f'{n} · {az:.0f}°', fill='black', font=F)
    S.save(SORT / nom)
lamina('LAMINA_C1_lent_5a1.png', "Filtres V92 (mirall) contra V91, compost EMULAT (sense capes d'ajust), marques roses de la V90, 5:1", [(8, 5), (55, 5), (80, 5), (240, 6), (262, 6), (285, 6), (300, 6)])
lamina('LAMINA_C1_linies_5a1.png', 'Filtres V92 contra V91, compost EMULAT, línies de la V88 (no han de tornar), 5:1', [(112, 5), (136, 5), (211, 5), (223, 5)])
print('fet')
